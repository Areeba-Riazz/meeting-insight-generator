from __future__ import annotations

# backend/src/main.py
from pathlib import Path
from dotenv import load_dotenv

# Load .env from backend folder (parent of src)
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

import sys
from functools import lru_cache
from pathlib import Path
from typing import List

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict
import uvicorn

# Ensure backend/src is on the import path when running from backend/
BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from src.api.routes import api_router  # noqa: E402
from src.utils.error_handlers import suppress_asyncio_socket_shutdown_errors  # noqa: E402

# Hard-coded CORS origins for simplicity (frontend localhost)
DEFAULT_CORS_ORIGINS = [
    "http://localhost:3000",  # same-port SPA or proxy
    "http://localhost:5173",  # Vite default dev server
]


class Settings(BaseSettings):
    api_host: str = "0.0.0.0"
    api_port: int = 3000
    debug: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow",  # tolerate unrelated env vars
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

app = FastAPI(title="Meeting Insight Generator API", debug=settings.debug)


@app.on_event("startup")
async def startup_event():
    """Configure error handling and database on startup."""
    suppress_asyncio_socket_shutdown_errors()
    print("[Startup] Socket shutdown error suppression enabled")
    
    # Automatically create database tables if they don't exist
    try:
        from src.core.database import ensure_tables_exist
        await ensure_tables_exist()
    except Exception as e:
        print(f"[Startup] Warning: Database initialization skipped: {e}")
        print("[Startup] App will continue to run (filesystem mode still available)")


# CORS configuration (fixed list)
# IMPORTANT: CORS middleware must be added BEFORE routers
# This ensures all responses (including errors) have CORS headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=DEFAULT_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Exception handlers to ensure CORS headers are always added
# Note: FastAPI's CORSMiddleware should handle this, but these ensure headers
# are present even if middleware fails
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Validation exception handler with CORS headers."""
    origin = request.headers.get("origin")
    headers = {}
    if origin and origin in DEFAULT_CORS_ORIGINS:
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Credentials"] = "true"
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
        headers=headers,
    )

# Routers
app.include_router(api_router)

# Serve storage folder as static files
storage_path = BASE_DIR / "storage"
storage_path.mkdir(exist_ok=True)
app.mount("/storage", StaticFiles(directory=str(storage_path)), name="storage")


@app.get("/", tags=["health"])
async def root() -> dict:
    return {
        "status": "ok",
        "service": "Meeting Insight Generator API",
        "host": settings.api_host,
        "port": settings.api_port,
    }


@app.get("/health", tags=["health"])
async def health() -> dict:
    return {"status": "ok"}


if __name__ == "__main__":
    # One-line launcher: python main.py
    uvicorn.run("main:app", host=settings.api_host, port=settings.api_port, reload=False)

