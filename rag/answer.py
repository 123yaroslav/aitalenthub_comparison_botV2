from typing import Dict, List
from rag.retrieve import hybrid

ALLOWED_TOPICS = [
    "магистр", "магистратура", "программа", "учебный план", "поступление", "ECTS", "ЗЕТ",
    "дисциплина", "курс", "модуль", "семестр", "выборные", "обязательные", "трек", "практика",
    "НИР", "лаборатория", "карьера", "требования", "пререквизиты"
]

def is_relevant(q: str, min_score: float = 0.8) -> bool:
    ql = q.lower()
    if any(t in ql for t in ALLOWED_TOPICS):
        return True
    # fall back to weak semantic check
    hits = hybrid(q, k=3)
    return any(h.get("score", 0) >= min_score for h in hits)

def answer(query: str, program: str | None = None) -> Dict:
    if not is_relevant(query):
        return {
            "text": "Я помогаю только по магистерским программам ИТМО «Искусственный интеллект» и «AI Product»: учебные планы, дисциплины, треки, ECTS, поступление. Задайте, пожалуйста, релевантный вопрос.",
            "citations": []
        }
    hits = hybrid(query, k=6)
    if program:
        hits = [h for h in hits if h.get("program") == program]
    if not hits:
        return {
            "text": "Не нашёл ответ в учебных планах. Уточните вопрос или попробуйте иначе сформулировать.",
            "citations": []
        }
    # Compose grounded answer
    bullets = []
    for h in hits[:4]:
        bullets.append(f"• {h['text']}  \n  ⮕ Цитата: {h['program']}, {h['source_ref']}")
    txt = "Вот что нашёл в учебных планах:\n" + "\n".join(bullets)
    return {"text": txt, "citations": [ {"source_url": h["source_url"], "source_ref": h["source_ref"]} for h in hits[:4] ]}
