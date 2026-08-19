import os
from pathlib import Path
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
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
COLLECTION_NAME = "iscor_knowledge_base"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

# Lazy-loaded globals to avoid loading model on every import/call
_model = None
_client = None

def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _model

def get_qdrant_client():
    global _client
    if _client is None:
        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        qdrant_api_key = os.getenv("QDRANT_API_KEY")
        _client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
    return _client


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
    Retrieves the top-k relevant chunks from Qdrant based on SHAP factors.
    Returns a dictionary with query used and retrieved chunks.
    """
    try:
        model = get_model()
        client = get_qdrant_client()
    except Exception as e:
        logging.warning(f"rag_degraded: Error loading model or DB - {e}")
        return {"query": "", "chunks": []}
        
    query = construct_query(shap_json)
    
    # Embed the query
    query_embedding = model.encode([query]).tolist()[0]
    
    # Search Qdrant
    try:
        results = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_embedding,
            limit=top_k
        )
    except Exception as e:
        logging.warning(f"rag_degraded: Error querying Qdrant - {e}")
        return {"query": query, "chunks": []}
    
    retrieved_chunks = []
    
    for point in results:
        meta = point.payload
        similarity = point.score
        
        chunk_info = {
            "chunk_id": meta["chunk_id"],
            "source": meta["source"],
            "document": meta["document"],
            "text": meta["text"],
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
        client = get_qdrant_client()
    except Exception as e:
        logging.warning(f"rag_degraded: Error loading model or DB - {e}")
        return []

    query_embedding = model.encode([query_text]).tolist()[0]
    
    try:
        results = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_embedding,
            limit=top_k
        )
    except Exception as e:
        logging.warning(f"rag_degraded: Error querying Qdrant - {e}")
        return []

    retrieved_chunks = []
    for point in results:
        retrieved_chunks.append(point.payload["text"])
            
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
