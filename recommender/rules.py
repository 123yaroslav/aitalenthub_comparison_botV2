from dataclasses import dataclass
from typing import List, Dict

@dataclass
class Profile:
    background: List[str]   # e.g., ["math-strong", "coding-basic", "product"]
    level: str              # "junior"|"middle"|"senior"
    interests: List[str]    # ["nlp","cv","recsys","security","mlops","analytics"]
    workload: str           # "low"|"medium"|"high"

# Map interests/background to elective keywords
KEYWORDS = {
    "math-strong": ["оптимизац", "статист", "вероят"],
    "coding-strong": ["инженер", "проектир", "систем", "разработ"],
    "product": ["продукт", "a/b", "метрик", "аналит"],
    "mlops": ["mlops", "pipeline", "инфраструкт", "деплой"],
    "security": ["безопас", "security"],
    "nlp": ["язык", "nlp", "text"],
    "cv": ["компьютерн", "зрение", "cv"],
    "recsys": ["рекоменд", "персонализац"],
    "analytics": ["аналит", "продукт", "метрик"],
}
