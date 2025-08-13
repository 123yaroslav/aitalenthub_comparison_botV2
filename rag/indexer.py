import json, os, sqlite3
from pathlib import Path
from typing import List, Dict
import chromadb
from chromadb.config import Settings
from rank_bm25 import BM25Okapi
from rag.embeddings import embed

BASE = Path(__file__).resolve().parent.parent
NORM = BASE / "data" / "normalized"
IDX = BASE / "data" / "index"
IDX.mkdir(parents=True, exist_ok=True)

def load_chunks() -> List[Dict]:
    chunks = []
    for name in ["AI.json", "AI_Product.json"]:
        p = NORM / name
        if not p.exists():
            continue
        data = json.loads(p.read_text(encoding="utf-8"))
        for c in data["courses"]:
            text = f"{c['name']} — {c['module']} — {c['ects']} ECTS — семестр {c['semester']}"
            chunks.append({
                "id": f"{data['program']}-{c['source_ref']}",
                "program": data["program"],
                "text": text,
                "source_ref": c["source_ref"],
                "source_url": data["source_url"]
            })
    return chunks

def build():
    chunks = load_chunks()
    if not chunks:
        print("[!] No normalized JSON found. Run `make scrape` first.")
        return

    # Vector index with Chroma
    client = chromadb.Client(Settings(is_persistent=True, persist_directory=str(IDX)))
    coll = client.get_or_create_collection("itmo_courses")
    coll.delete(where={})
    embeddings = embed([ch["text"] for ch in chunks])
    ids = [ch["id"] for ch in chunks]
    metadatas = [{"program": ch["program"], "source_ref": ch["source_ref"], "source_url": ch["source_url"]} for ch in chunks]
    coll.add(ids=ids, embeddings=embeddings, metadatas=metadatas, documents=[ch["text"] for ch in chunks])

    # BM25 index (simple serialized object)
    corpus = [ch["text"] for ch in chunks]
    bm25 = BM25Okapi([t.split() for t in corpus])
    import pickle
    with open(IDX / "bm25.pkl", "wb") as f:
        pickle.dump({"bm25": bm25, "chunks": chunks}, f)
    print(f"[i] Built vector and BM25 indexes with {len(chunks)} chunks")

if __name__ == "__main__":
    build()
