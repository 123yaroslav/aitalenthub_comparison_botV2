from fastapi import FastAPI
from pydantic import BaseModel
from rag.answer import answer
from recommender.engine import pick_electives
from recommender.rules import Profile

app = FastAPI(title="ITMO Masters Advisor API")

class Ask(BaseModel):
    query: str
    program: str | None = None

@app.post("/ask")
def ask(a: Ask):
    return answer(a.query, a.program)

class RecReq(BaseModel):
    background: list[str]
    level: str
    interests: list[str]
    workload: str
    program: str

@app.post("/recommend")
def recommend(r: RecReq):
    prof = Profile(r.background, r.level, r.interests, r.workload)
    return pick_electives(prof, r.program)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
