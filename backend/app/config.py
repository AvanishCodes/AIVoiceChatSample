import os
from pathlib import Path
from typing import Literal, Optional
from pydantic import ConfigDict
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App Information
    APP_NAME: str = "FleetPanda Voice & Chat Support Agent"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: list[str] = ["*"]

    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    DATA_DIR: Path = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
    DATABASE_PATH: Path = Path(os.getenv("DATABASE_PATH", DATA_DIR / "dispatch.db"))

    # Authentication & JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "fleetpanda-super-secret-jwt-key-2026-secure")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # LLM Provider Configuration
    # Supported: "ollama", "openai", "gemini", "anthropic"
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "ollama")
    
    # Ollama Settings
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.2")
    
    # Cloud Provider Settings
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY", None)
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")
    
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", None))
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
    
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY", None)
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")

    # MCP Server Settings
    MCP_SERVER_URL: str = os.getenv("MCP_SERVER_URL", "http://127.0.0.1:8000/api/mcp")
    MCP_INTERNAL_SECRET: str = os.getenv("MCP_INTERNAL_SECRET", "fleetpanda-mcp-internal-secret-token")

    # Voice / Audio Settings
    DEFAULT_TTS_VOICE: str = "en-US-JennyNeural"
    
    model_config = ConfigDict(extra="ignore")

settings = Settings()

# Ensure DATA_DIR and DB paths are resolved properly if relative
if not settings.DATABASE_PATH.exists():
    # Try finding in current directory or parent directory
    alt_paths = [
        Path("data/dispatch.db"),
        Path("../data/dispatch.db"),
        Path("/app/data/dispatch.db"),
        settings.BASE_DIR / "data" / "dispatch.db"
    ]
    for p in alt_paths:
        if p.exists():
            settings.DATABASE_PATH = p.resolve()
            settings.DATA_DIR = p.parent.resolve()
            break
