from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class NLQueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500, description="Natural language business question")

class NLQueryResponse(BaseModel):
    question: str
    generated_sql: str
    is_safe: bool
    refused: bool = Field(
        default=False,
        description="True when the question was outside the supported scope and no SQL was generated or executed.",
    )
    row_count: int
    data: List[Dict[str, Any]]
    explanation: str


# --- EcomAI Analyst (simple, grounded) ---

class AIAnalystRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500, description="Natural language business question")

class AIAnalystResponse(BaseModel):
    question: str
    analysis: Dict[str, Any]
    gemini_response: str
    generated_at: str
    disclaimer: str
