import os
import re
from pathlib import Path
import fitz  # PyMuPDF
from sentence_transformers import SentenceTransformer
import chromadb

BASE_DIR = Path(__file__).resolve().parent.parent
KNOWLEDGE_BASE_DIR = BASE_DIR / "knowledge_base"
VECTOR_DB_DIR = BASE_DIR / "vector_db"

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
    # Remove repeated newlines
    text = re.sub(r'\n+', '\n', text)
    # Remove extra spaces
    text = re.sub(r' +', ' ', text)
    # Remove URLs (simplified regex)
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
    """Reads PDFs, chunks them, embeds them, and stores in ChromaDB."""
    print(f"Initializing embedding model: {EMBEDDING_MODEL_NAME}...")
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    
    print(f"Initializing ChromaDB at {VECTOR_DB_DIR}...")
    chroma_client = chromadb.PersistentClient(path=str(VECTOR_DB_DIR))
    
    # We will reset or get the collection. For this script, we'll recreate it.
    try:
        chroma_client.delete_collection(name=COLLECTION_NAME)
    except Exception:
        pass  # Collection doesn't exist
        
    collection = chroma_client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"} # Use cosine similarity
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
                    
                # Generate IDs, embeddings, and metadata for Chroma
                ids = []
                metadatas = []
                documents = []
                
                for idx, chunk in enumerate(chunks):
                    chunk_id = f"{source_org}_{doc_title}_{idx:03d}"
                    ids.append(chunk_id)
                    documents.append(chunk)
                    metadatas.append({
                        "source": source_org,
                        "document": doc_title,
                        "chunk_index": idx
                    })
                    
                # Embed chunks
                embeddings = model.encode(documents).tolist()
                
                # Add to ChromaDB
                collection.add(
                    ids=ids,
                    embeddings=embeddings,
                    documents=documents,
                    metadatas=metadatas
                )
                
                total_chunks += len(chunks)
                print(f"  -> Added {len(chunks)} chunks.")
                
    print(f"\nIngestion complete! Total chunks stored: {total_chunks}")
    print(f"Vector DB is ready at {VECTOR_DB_DIR}")


if __name__ == "__main__":
    if not KNOWLEDGE_BASE_DIR.exists():
        print(f"Error: {KNOWLEDGE_BASE_DIR} does not exist.")
    else:
        ingest_knowledge_base()
