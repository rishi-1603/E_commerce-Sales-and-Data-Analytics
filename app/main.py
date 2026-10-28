from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
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

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize DB schema and seed CSV data if empty
    logger.info("Initializing Commerce Intelligence API...")
    init_db()
    logger.info("Commerce Intelligence API ready.")
    yield
    # Shutdown logic
    logger.info("Commerce Intelligence API shut down.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="A high-performance Python backend service for reliable e-commerce analytics, validated business metrics, and AST-secured natural language querying.",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Structured Request ID Middleware
app.add_middleware(RequestIDMiddleware)

# Root endpoint
@app.get("/", tags=["System"])
def root():
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/health",
        "api_v1": settings.API_V1_STR
    }

# Include routers
app.include_router(health_router, prefix="", tags=["System"])
app.include_router(api_router, prefix=settings.API_V1_STR)
