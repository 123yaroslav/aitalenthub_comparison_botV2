import json
from pathlib import Path
from typing import Dict, List
from .rules import Profile, KEYWORDS

BASE = Path(__file__).resolve().parent.parent

def load_plan(program: str) -> Dict:
    p = BASE / "data" / "normalized" / f"{program.replace(' ','_')}.json"
    return json.loads(p.read_text(encoding="utf-8"))

def pick_electives(profile: Profile, program: str) -> Dict[str, List[Dict]]:
    plan = load_plan(program)
    electives = [c for c in plan["courses"] if c["type"] == "elective"]
    # Score by keyword matches
    def score_course(c):
        name = c["name"].lower()
        score = 0
        for key in profile.background + profile.interests:
            for kw in KEYWORDS.get(key, []):
                if kw in name:
                    score += 2
        return score
    scored = sorted([(score_course(c), c) for c in electives], key=lambda x: x[0], reverse=True)
    pri = [c for s,c in scored if s>=2][:3]
    sec = [c for s,c in scored if 1<=s<2][:3]
    stretch = [c for s,c in scored if s==0][:3]
    # Respect ECTS limit rough suggestion
    return {
        "primary": pri,
        "secondary": sec,
        "stretch": stretch
    }
