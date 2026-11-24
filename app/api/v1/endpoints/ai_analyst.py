"""
AI Analyst endpoint — simple, grounded business analysis.
=========================================================
User asks question → Python calculates KPIs → Gemini explains → response.
"""
import logging

from fastapi import APIRouter, HTTPException

from app.schemas.query import AIAnalystRequest, AIAnalystResponse
from app.services.analytics_ai_service import AnalyticsAIService

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/ai-analyst", response_model=AIAnalystResponse, tags=["AI Analyst"])
async def ask_ai_analyst(request: AIAnalystRequest):
    """
    EcomAI Business Analyst: ask any business question.

    Architecture:
    1. Python determines relevant analysis from the question
    2. Pandas calculates verified KPIs from data/processed/*.csv
    3. Results sent to Gemini for professional business interpretation
    4. Returns analysis + Gemini explanation

    The LLM NEVER calculates - it only interprets verified Python results.
    All numbers come from the dataset, respecting metric definitions in data/metrics.json.
    """
    try:
        result = AnalyticsAIService.ask(request.question)
        return AIAnalystResponse(**result)
    except ValueError as e:
        if "GEMINI_API_KEY" in str(e):
            raise HTTPException(
                status_code=503,
                detail="AI Analyst unavailable: GEMINI_API_KEY not configured on server"
            )
        logger.warning("AI analyst validation error: %s", e)
        raise HTTPException(status_code=400, detail="Invalid request.")
    except Exception:
        logger.exception("AI analyst failed")
        raise HTTPException(status_code=500, detail="Analysis failed.")