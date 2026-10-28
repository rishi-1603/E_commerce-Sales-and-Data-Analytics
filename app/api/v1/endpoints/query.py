from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.query import NLQueryRequest, NLQueryResponse
from app.services.query_service import QueryService

router = APIRouter()

@router.post("/nl-to-sql", response_model=NLQueryResponse, tags=["AI Analytics"])
async def execute_natural_language_query(
    request: NLQueryRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Enterprise-grade Natural Language to SQL Assistant:
    1. Interprets natural language questions within the e-commerce schema.
    2. Generates validated SQL queries.
    3. Enforces AST security validation (sqlglot): strictly read-only SELECT, whitelisted tables, and injected LIMIT.
    4. Executes query and returns grounded data with an explanation.
    """
    return await QueryService.process_natural_language_query(db, request.question)
