import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.config import settings
from app.db.session import init_db
from app.api.v1.router import api_router
from app.api.v1.endpoints.health import router as health_router
from app.middleware.request_id import RequestIDMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("commerce_api")

# Optional API-key gate: only enforced when API_KEY is set in the environment.
# Unset (the default) keeps the app an open, runnable showcase.
_API_KEY = os.getenv("API_KEY")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Commerce Intelligence API...")
    init_db()
    logger.info("Commerce Intelligence API ready.")
    yield
    logger.info("Commerce Intelligence API shut down.")


# Docs are only exposed in development to avoid schema enumeration in prod.
_docs_url = "/docs" if os.getenv("ENV", "development").lower() == "development" else None
_redoc_url = "/redoc" if os.getenv("ENV", "development").lower() == "development" else None

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="A high-performance Python backend service for reliable e-commerce analytics, validated business metrics, and AST-secured natural language querying.",
    lifespan=lifespan,
    docs_url=_docs_url,
    redoc_url=_redoc_url,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-API-Key", "X-Request-ID"],
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'",
        )
        return response


class OptionalAPIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if _API_KEY and request.url.path.startswith("/api/"):
            if request.headers.get("X-API-Key") != _API_KEY:
                return Response(status_code=401, content="Unauthorized")
        return await call_next(request)


# Structured Request ID Middleware
app.add_middleware(RequestIDMiddleware)
# Security hardening (outermost last so headers apply to all responses)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(OptionalAPIKeyMiddleware)

# Root endpoint
@app.get("/", tags=["System"])
def root():
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs" if _docs_url else None,
        "health": "/health",
        "api_v1": settings.API_V1_STR,
    }

# Include routers
app.include_router(health_router, prefix="", tags=["System"])
app.include_router(api_router, prefix=settings.API_V1_STR)
