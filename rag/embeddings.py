import os
from typing import List
from utils import env

_provider = env("EMBEDDINGS_PROVIDER", "local")

if _provider == "openai":
    # Lazy import / pseudo-interface. Users must set OPENAI_API_KEY.
    from openai import OpenAI
    client = OpenAI()
    def embed(texts: List[str]) -> List[List[float]]:
        res = client.embeddings.create(
            input=texts, model="text-embedding-3-small"
        )
        return [d.embedding for d in res.data]
else:
    from sentence_transformers import SentenceTransformer
    _model = SentenceTransformer("BAAI/bge-m3")
    def embed(texts: List[str]) -> List[List[float]]:
        return _model.encode(texts, normalize_embeddings=True).tolist()
