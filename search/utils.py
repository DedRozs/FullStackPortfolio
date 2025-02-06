import faiss
import numpy as np
import pickle
from sentence_transformers import SentenceTransformer
from search.models import SearchIndex

# Load SBERT model
model = SentenceTransformer("all-MiniLM-L6-v2")

# FAISS index storage path
FAISS_INDEX_FILE = "faiss_index.pkl"

def generate_embedding(text):
    """Generate an embedding for the given text using SBERT."""
    return model.encode([text])[0]

def save_faiss_index():
    """Save FAISS index with all stored embeddings."""
    texts = []
    embeddings = []

    for item in SearchIndex.objects.all():
        texts.append(item.text)
        embeddings.append(np.frombuffer(item.embedding, dtype=np.float32))

    if embeddings:
        index = faiss.IndexFlatL2(len(embeddings[0]))
        index.add(np.array(embeddings))
        
        with open(FAISS_INDEX_FILE, "wb") as f:
            pickle.dump((index, texts), f)

def load_faiss_index():
    """Load FAISS index from storage."""
    try:
        with open(FAISS_INDEX_FILE, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return None, []

def search_similar(query, top_k=5):
    """Perform FAISS-based similarity search."""
    query_embedding = np.array([generate_embedding(query)], dtype=np.float32)

    index, texts = load_faiss_index()
    if index is None:
        return []

    _, indices = index.search(query_embedding, top_k)
    return [texts[i] for i in indices[0] if i < len(texts)]
