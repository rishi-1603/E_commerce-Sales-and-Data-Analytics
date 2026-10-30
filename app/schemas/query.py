from pydantic import BaseModel, Field
from typing import List, Dict, Any

class NLQueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500, description="Natural language business question")

class NLQueryResponse(BaseModel):
    question: str
    generated_sql: str
    is_safe: bool
    row_count: int
    data: List[Dict[str, Any]]
    explanation: str
