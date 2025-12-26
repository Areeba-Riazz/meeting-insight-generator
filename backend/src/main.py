from functools import lru_cache
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic_settings import BaseSettings, SettingsConfigDict

from .api.routes import api_router
from .utils.error_handlers import suppress_asyncio_socket_shutdown_errors

class Settings(BaseSettings):
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True
    cors_origins: List[str] = ["*"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()

app = FastAPI(title="Meeting Insight Generator API", debug=settings.debug)

# Suppress harmless asyncio socket shutdown errors during streaming
# This reduces log noise when clients disconnect during video streaming
suppress_asyncio_socket_shutdown_errors()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(api_router)

@app.get("/health", tags=["health"])
async def health() -> dict:
    return {"status": "ok"}