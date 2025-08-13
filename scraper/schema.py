from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Dict

CourseType = Literal["required", "elective"]

class Course(BaseModel):
    code: Optional[str] = None
    name: str
    semester: int
    ects: float
    type: CourseType
    module: str
    prerequisites: List[str] = []
    notes: Optional[str] = None
    source_ref: str = Field(..., description="e.g., pdf:page=12,row=5")

class Rules(BaseModel):
    total_ects: int
    min_electives_ects: int
    per_semester_constraints: Dict[str, Dict[str, int]]

class Plan(BaseModel):
    program: Literal["AI", "AI Product"]
    version: str
    source_url: str
    courses: List[Course]
    rules: Rules
