"""
FastAPI application — Phase 4: analytics router added.
"""

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from dotenv import load_dotenv

load_dotenv()

from .routes.chat      import router as chat_router
from .routes.health    import router as health_router
from .routes.analytics import router as analytics_router   # NEW
from .services.rag     import configure_gemini

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent))
from database.supabase_client import get_client

logger = logging.getLogger(__name__)

logging.basicConfig(
    level   = os.getenv("LOG_LEVEL", "INFO").upper(),
    format  = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt = "%H:%M:%S",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting GitLab Handbook AI backend ...")

    required = ["GEMINI_API_KEY", "SUPABASE_URL", "SUPABASE_SERVICE_KEY"]
    missing  = [k for k in required if not os.getenv(k)]
    if missing:
        raise RuntimeError(f"Missing env vars: {', '.join(missing)}")

    configure_gemini(os.environ["GEMINI_API_KEY"])

    db = get_client(
        url = os.environ["SUPABASE_URL"],
        key = os.environ["SUPABASE_SERVICE_KEY"],
    )

    try:
        result = db.table("documents").select("id").limit(1).execute()
        logger.info(f"Supabase connected — documents table reachable")
    except Exception as e:
        logger.warning(f"Supabase connection check failed: {e}")

    app.state.db = db
    logger.info("Backend ready")
    yield
    logger.info("Backend shutting down")


def create_app() -> FastAPI:
    app = FastAPI(
        title       = "GitLab Handbook AI",
        description = "GenAI chatbot for GitLab Handbook and Direction pages.",
        version     = "1.0.0",
        docs_url    = "/docs",
        redoc_url   = "/redoc",
        lifespan    = lifespan,
    )

    allowed_origins_raw = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:5173,http://localhost:3000",
    )
    allowed_origins = [o.strip() for o in allowed_origins_raw.split(",") if o.strip()]

    app.add_middleware(
        CORSMiddleware,
        allow_origins     = allowed_origins,
        allow_credentials = True,
        allow_methods     = ["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers     = ["*"],
        expose_headers    = ["X-Session-Id"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    app.include_router(chat_router,      prefix="/api/v1")
    app.include_router(health_router,    prefix="/api/v1")
    app.include_router(analytics_router, prefix="/api/v1")   # NEW

    @app.get("/", include_in_schema=False)
    async def root():
        return {
            "name":      "GitLab Handbook AI",
            "version":   "1.0.0",
            "docs":      "/docs",
            "health":    "/api/v1/health",
            "analytics": "/api/v1/analytics/summary",
        }

    return app


app = create_app()