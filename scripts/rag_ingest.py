import os
import re
import uuid
from pathlib import Path
import fitz  # PyMuPDF
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct

BASE_DIR = Path(__file__).resolve().parent.parent
KNOWLEDGE_BASE_DIR = BASE_DIR / "knowledge_base"

# RAG Configuration
CHUNK_SIZE_WORDS = 450
OVERLAP_WORDS = 50
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
COLLECTION_NAME = "iscor_knowledge_base"


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extracts raw text from a PDF file using PyMuPDF."""
    text = ""
    try:
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text() + "\n"
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
    return text


def clean_text(text: str) -> str:
    """Cleans the extracted text."""
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r' +', ' ', text)
    text = re.sub(r'http[s]?://\S+', '', text)
    return text.strip()


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Splits text into chunks of `chunk_size` words with `overlap` words."""
    words = text.split()
    chunks = []
    
    if not words:
        return chunks
        
    i = 0
    while i < len(words):
        chunk_words = words[i:i + chunk_size]
        chunks.append(" ".join(chunk_words))
        i += (chunk_size - overlap)
        
    return chunks


def ingest_knowledge_base():
    """Reads PDFs, chunks them, embeds them, and stores in Qdrant Cloud."""
    print(f"Initializing embedding model: {EMBEDDING_MODEL_NAME}...")
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    
    print(f"Initializing QdrantClient at {qdrant_url}...")
    client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
    
    print(f"Recreating collection {COLLECTION_NAME}...")
    # all-MiniLM-L6-v2 has a vector size of 384
    client.recreate_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    )
    
    total_chunks = 0
    
    print(f"Scanning {KNOWLEDGE_BASE_DIR} for PDFs...")
    for root, _, files in os.walk(KNOWLEDGE_BASE_DIR):
        for file in files:
            if file.lower().endswith(".pdf"):
                pdf_path = Path(root) / file
                source_org = pdf_path.parent.name
                doc_title = pdf_path.stem
                
                print(f"Processing: {source_org} / {doc_title}")
                
                raw_text = extract_text_from_pdf(pdf_path)
                cleaned_text = clean_text(raw_text)
                chunks = chunk_text(cleaned_text, CHUNK_SIZE_WORDS, OVERLAP_WORDS)
                
                if not chunks:
                    continue
                    
                points = []
                for idx, chunk in enumerate(chunks):
                    chunk_id_str = f"{source_org}_{doc_title}_{idx:03d}"
                    point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk_id_str))
                    
                    # Embed single chunk (in production, batch embed)
                    embedding = model.encode(chunk).tolist()
                    
                    points.append(
                        PointStruct(
                            id=point_id,
                            vector=embedding,
                            payload={
                                "chunk_id": chunk_id_str,
                                "source": source_org,
                                "document": doc_title,
                                "chunk_index": idx,
                                "text": chunk
                            }
                        )
                    )
                
                # Add to Qdrant
                client.upsert(
                    collection_name=COLLECTION_NAME,
                    points=points
                )
                
                total_chunks += len(chunks)
                print(f"  -> Added {len(chunks)} chunks.")
                
    print(f"\nIngestion complete! Total chunks stored: {total_chunks}")


if __name__ == "__main__":
    if not KNOWLEDGE_BASE_DIR.exists():
        print(f"Error: {KNOWLEDGE_BASE_DIR} does not exist.")
    else:
        ingest_knowledge_base()
