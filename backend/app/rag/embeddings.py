import threading
from sentence_transformers import SentenceTransformer

_model = None
_model_lock = threading.Lock()

def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model

def embed(text: str) -> list[float]:
    model = get_model()
    vec = model.encode(text, normalize_embeddings=True)
    return vec.tolist()

def embed_batch(texts: list[str]) -> list[list[float]]:
    model = get_model()
    vecs = model.encode(texts, normalize_embeddings=True)
    return vecs.tolist()
