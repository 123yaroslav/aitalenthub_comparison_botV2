from typing import List, Dict, Tuple
import json, pickle, os
from pathlib import Path
import chromadb
from chromadb.config import Settings
from rag.embeddings import embed
from rank_bm25 import BM25Okapi

BASE = Path(__file__).resolve().parent.parent
IDX = BASE / "data" / "index"

def bm25_search(query: str, k: int = 8) -> List[Dict]:
    pkl = IDX / "bm25.pkl"
    chunks: List[Dict]
    if pkl.exists():
        with open(pkl, "rb") as f:
            data = pickle.load(f)
        bm25 = data["bm25"]
        chunks = data["chunks"]
    else:
        # Lightweight on-the-fly BM25 using normalized JSON if indexes are missing
        base = BASE
        norm = base / "data" / "normalized"
        chunks = []
        for name in ["AI.json", "AI_Product.json"]:
            p = norm / name
            if not p.exists():
                continue
            data = json.loads(p.read_text(encoding="utf-8"))
            for c in data.get("courses", []):
                text = f"{c['name']} — {c.get('module','')} — {c.get('ects',0)} ECTS — семестр {c.get('semester','')}"
                chunks.append({
                    "id": f"{data['program']}-{c['source_ref']}",
                    "program": data["program"],
                    "text": text,
                    "source_ref": c["source_ref"],
                    "source_url": data.get("source_url", "")
                })
        if not chunks:
            return []
        corpus_tokens = [ch["text"].split() for ch in chunks]
        bm25 = BM25Okapi(corpus_tokens)
    scores = bm25.get_scores(query.split())
    pairs = sorted(zip(chunks, scores), key=lambda x: x[1], reverse=True)[:k]
    out = []
    for ch, sc in pairs:
        ch2 = dict(ch)
        ch2["score_bm25"] = float(sc)
        out.append(ch2)
    return out

def vector_search(query: str, k: int = 8) -> List[Dict]:
    try:
        client = chromadb.Client(Settings(is_persistent=True, persist_directory=str(IDX)))
        coll = client.get_collection("itmo_courses")
    except Exception:
        return []
    qvec = embed([query])[0]
    res = coll.query(query_embeddings=[qvec], n_results=k)
    out = []
    for i in range(len(res.get("ids", [[]])[0])):
        out.append({
            "id": res["ids"][0][i],
            "text": res["documents"][0][i],
            "source_ref": res["metadatas"][0][i]["source_ref"],
            "source_url": res["metadatas"][0][i]["source_url"],
            "program": res["metadatas"][0][i]["program"],
            "score_vec": float(res.get("distances", [[0.0]])[0][i])
        })
    return out

def hybrid(query: str, k: int = 6) -> List[Dict]:
    a = bm25_search(query, k*2)
    b = vector_search(query, k*2)
    # simple fusion by normalized ranks
    def rank_dict(lst, key):
        return {lst[i]["id"]: i for i in range(len(lst))}
    ra = rank_dict(a, "score_bm25") if a else {}
    rb = rank_dict(b, "score_vec") if b else {}
    merged = {}
    for item in (a + b):
        rid = item["id"]
        merged.setdefault(rid, {"item": item, "ra": 1e6, "rb": 1e6})
        if "score_bm25" in item:
            merged[rid]["ra"] = min(merged[rid]["ra"], ra.get(rid, 1e6))
        if "score_vec" in item:
            merged[rid]["rb"] = min(merged[rid]["rb"], rb.get(rid, 1e6))
    scored = []
    for rid, v in merged.items():
        score = 1/(1+v["ra"]) + 1/(1+v["rb"])
        it = v["item"]
        it["score"] = float(score)
        scored.append(it)
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:k]
