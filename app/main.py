from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os

APP_VERSION = "0.1.0"

app = FastAPI(
    title="Contrast Finance 2.0 API",
    version=APP_VERSION,
    description="Backend API for Contrast Finance 2.0",
)

# For the first dev launch we keep CORS open.
# Later we will restrict this to the real frontend domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class HealthResponse(BaseModel):
    ok: bool
    service: str
    version: str
    environment: str
    database_configured: bool


@app.get("/", tags=["system"])
def root():
    return {
        "ok": True,
        "service": "contrast-finance-api",
        "message": "Contrast Finance 2.0 API is running",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", response_model=HealthResponse, tags=["system"])
def health():
    return HealthResponse(
        ok=True,
        service="contrast-finance-api",
        version=APP_VERSION,
        environment=os.getenv("APP_ENV", "dev"),
        database_configured=bool(os.getenv("DATABASE_URL")),
    )
