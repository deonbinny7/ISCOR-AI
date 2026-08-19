import os
from pathlib import Path
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import logging

# Feature name mapping for cleaner queries
FEATURE_DISPLAY_NAMES = {
    "Age": "Age",
    "Gender": "Gender",
    "Sleep_Hours": "Sleep Hours",
    "Academic_Pressure": "Academic Pressure",
    "Financial_Stress": "Financial Stress",
    "Social_Support": "Social Support",
    "Study_Hours": "Study Hours",
    "Physical_Activity": "Exercise",
    "Family_History": "Family History of Mental Illness",
    "Stress_Index": "Overall Stress",
    "Lifestyle_Score": "Overall Lifestyle",
    "Academic_Load": "Academic Workload",
}

BASE_DIR = Path(__file__).resolve().parents[1]
VECTOR_DB_DIR = Path(os.getenv("ISCOR_VECTOR_DB_DIR", str(BASE_DIR / "vector_db")))
COLLECTION_NAME = "iscor_knowledge_base"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

# Lazy-loaded globals to avoid loading model on every import/call
_model = None
_collection = None

def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _model

def get_collection():
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=str(VECTOR_DB_DIR))
        _collection = client.get_collection(name=COLLECTION_NAME)
    return _collection


def construct_query(shap_json: dict) -> str:
    """
    Constructs a semantic search query based on Risk Level and Top SHAP factors.
    """
    risk_label = shap_json["risk_label"]
    
    factors_str = ""
    for f in shap_json["top_factors"]:
        display_name = FEATURE_DISPLAY_NAMES.get(f["feature"], f["feature"])
        arrow = "↑" if f["direction"] == "increases_risk" else "↓"
        factors_str += f"{display_name} {arrow}, "
        
    factors_str = factors_str.rstrip(", ")
    
    query = f"Risk: {risk_label}, Top Factors: {factors_str}. Need Evidence-based student wellness recommendations."
    return query


def retrieve_evidence(shap_json: dict, top_k: int = 5) -> dict:
    """
    Retrieves the top-k relevant chunks from ChromaDB based on SHAP factors.
    Returns a dictionary with query used and retrieved chunks.
    """
    try:
        model = get_model()
        collection = get_collection()
    except Exception as e:
        logging.warning(f"rag_degraded: Error loading model or DB - {e}")
        return {"query": "", "chunks": []}
        
    query = construct_query(shap_json)
    
    # Embed the query
    query_embedding = model.encode([query]).tolist()
    
    # Search ChromaDB
    try:
        results = collection.query(
            query_embeddings=query_embedding,
            n_results=top_k
        )
    except Exception as e:
        logging.warning(f"rag_degraded: Error querying ChromaDB - {e}")
        return {"query": query, "chunks": []}
    
    retrieved_chunks = []
    
    if results["documents"] and results["documents"][0]:
        for i in range(len(results["documents"][0])):
            doc = results["documents"][0][i]
            meta = results["metadatas"][0][i]
            # ChromaDB returns distances for cosine (lower is closer). We can convert to similarity (1 - distance).
            # The 'distances' key is present if returned.
            distance = results["distances"][0][i] if "distances" in results else 0
            similarity = 1.0 - distance
            
            chunk_info = {
                "chunk_id": f"{meta['source']}_{meta['document']}_{meta['chunk_index']}",
                "source": meta["source"],
                "document": meta["document"],
                "text": doc,
                "similarity_score": round(float(similarity), 4)
            }
            retrieved_chunks.append(chunk_info)
            
    return {
        "query": query,
        "chunks": retrieved_chunks
    }

def search_knowledge_base(query_text: str, top_k: int = 3) -> list:
    """
    Searches the vector DB using a plain text query.
    Useful for the Wellness Companion.
    """
    try:
        model = get_model()
        collection = get_collection()
    except Exception as e:
        logging.warning(f"rag_degraded: Error loading model or DB - {e}")
        return []

    query_embedding = model.encode([query_text]).tolist()
    
    try:
        results = collection.query(
            query_embeddings=query_embedding,
            n_results=top_k
        )
    except Exception as e:
        logging.warning(f"rag_degraded: Error querying ChromaDB - {e}")
        return []

    retrieved_chunks = []
    if results["documents"] and results["documents"][0]:
        for i in range(len(results["documents"][0])):
            doc = results["documents"][0][i]
            retrieved_chunks.append(doc)
            
    return retrieved_chunks


if __name__ == "__main__":
    # Test retrieval
    test_shap = {
        "risk_label": "Moderate",
        "top_factors": [
            {"feature": "Sleep_Hours", "direction": "decreases_risk"},
            {"feature": "Academic_Pressure", "direction": "increases_risk"},
            {"feature": "Physical_Activity", "direction": "decreases_risk"},
        ]
    }
    
    import time
    start = time.time()
    result = retrieve_evidence(test_shap)
    latency = (time.time() - start) * 1000
    
    print(f"Query used: {result['query']}")
    print(f"Latency: {latency:.1f}ms")
    print(f"Retrieved {len(result['chunks'])} chunks:")
    for c in result['chunks']:
        print(f" - [{c['similarity_score']}] {c['source']}/{c['document']}: {c['text'][:100]}...")
