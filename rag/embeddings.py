import os
from typing import List
from utils import env

_provider = env("EMBEDDINGS_PROVIDER", "local").lower()

if _provider == "openai":
    # Lazy client; users must set OPENAI_API_KEY.
    from openai import OpenAI
    client = OpenAI()
    def embed(texts: List[str]) -> List[List[float]]:
        res = client.embeddings.create(input=texts, model="text-embedding-3-small")
        return [d.embedding for d in res.data]
elif _provider == "mock":
    # Deterministic small vectors for tests/CI without heavyweight downloads.
    def embed(texts: List[str]) -> List[List[float]]:
        return [[0.0] * 8 for _ in texts]
else:
    _model = None
    def embed(texts: List[str]) -> List[List[float]]:
        global _model
        if _model is None:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer("BAAI/bge-m3")
        return _model.encode(texts, normalize_embeddings=True).tolist()
