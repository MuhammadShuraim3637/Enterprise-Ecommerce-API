from typing import Dict
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from fastapi.staticfiles import StaticFiles
# 1. Purane auth_router ki jagah naya central api_router import kiya
from app.api.v1.api import api_router 

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    version="1.0.0",
)

# Cross-Origin Resource Sharing settings for headless architectures
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict this to specific domains in staging/production environments
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
# 2. Central API Router ko yahan include kar diya, ab saare endpoints (/auth, /users) is ke andar se chalenge
app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["System"])
async def health_check() -> Dict[str, str]:
    """
    Standard heartbeat endpoint for container orchestration readiness probes.
    """
    return {"status": "healthy", "app": settings.APP_NAME}