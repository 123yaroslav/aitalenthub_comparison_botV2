import json, os, pathlib

BASE = pathlib.Path(__file__).resolve().parents[1]

def test_normalized_exists():
    f1 = BASE / "data" / "normalized" / "AI.json"
    f2 = BASE / "data" / "normalized" / "AI_Product.json"
    assert f1.exists() and f2.exists(), "Run `make scrape` first to create normalized JSON files."

def test_total_ects_reasonable():
    for name in ["AI.json", "AI_Product.json"]:
        data = json.loads((BASE / "data" / "normalized" / name).read_text(encoding="utf-8"))
        total = sum(c["ects"] for c in data["courses"])
        assert total >= 100, f"ECTS too low in {name}: {total}"
