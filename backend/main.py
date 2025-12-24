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

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic_settings import BaseSettings, SettingsConfigDict
import uvicorn

# Ensure backend/src is on the import path when running from backend/
BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from src.api.routes import api_router  # noqa: E402

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

# CORS configuration (fixed list)
app.add_middleware(
    CORSMiddleware,
    allow_origins=DEFAULT_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

