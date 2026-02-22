from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from database import engine, Base
from config import get_settings
from agents.router import router as agents_router
from agents.factory_router import router as factory_router
from intelligence.router import router as intelligence_router
from monitoring.router import router as monitoring_router
from ui import router as ui_router

settings = get_settings()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)

    # Seed default agents
    logger.info("Seeding default agents...")
    from seed import load_default_agents
    load_default_agents()

    logger.info("Database ready.")
    yield
    # Shutdown
    logger.info("Shutting down...")


app = FastAPI(
    title="Personal AI OS",
    description="Spec-driven agent platform with RAG, monitoring, and nightly loops",
    version="0.1.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(agents_router, prefix="/api/agents", tags=["Agents"])
app.include_router(factory_router, prefix="/api/factory", tags=["Factory"])
app.include_router(intelligence_router, prefix="/api", tags=["Intelligence"])
app.include_router(monitoring_router, prefix="/api", tags=["Monitoring"])


# UI routes (must be after API routes)
app.include_router(ui_router, tags=["UI"])


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": "0.1.0"}
