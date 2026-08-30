import logging
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes_audio import audio_router
from app.api.routes_auth import auth_router
from app.api.routes_chat import chat_router
from app.api.routes_health import health_router
from app.api.routes_sql import sql_router
from app.api.routes_triage import triage_router
from app.config import settings
from app.mcp.server import mcp_router

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("fleetpanda.main")

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"🚀 {settings.APP_NAME} started successfully!")
    logger.info(f"📂 Database path: {settings.DATABASE_PATH}")
    logger.info(f"🤖 LLM Provider: {settings.LLM_PROVIDER}")
    yield
    logger.info("🛑 Shutting down FleetPanda Voice & Chat Support Agent.")

# FastAPI App
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="FleetPanda Voice & Chat Support Agent with Multi-Tenant Isolation and Custom MCP Server.",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(auth_router)
app.include_router(mcp_router)
app.include_router(chat_router)
app.include_router(sql_router)
app.include_router(triage_router)
app.include_router(audio_router)
app.include_router(health_router)

# Mount frontend build static files if present
frontend_dist_dirs = [
    Path(__file__).parent.parent.parent / "frontend" / "dist",
    Path("/app/frontend_dist"),
    Path("./frontend/dist"),
]

for dist_dir in frontend_dist_dirs:
    if dist_dir.exists() and (dist_dir / "index.html").exists():
        logger.info(f"Mounting static frontend build from: {dist_dir}")
        app.mount("/", StaticFiles(directory=str(dist_dir), html=True), name="static_frontend")
        break


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
