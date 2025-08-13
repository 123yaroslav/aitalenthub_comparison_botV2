import json, pathlib
from rag.answer import answer

BASE = pathlib.Path(__file__).resolve().parents[1]

def test_relevancy_filter():
    res = answer("погода в Питере?")
    assert "только по магистерским программам" in res["text"]

def test_answer_contains_source_refs():
    res = answer("какие выборные доступны?")
    assert "Цитата:" in res["text"]
