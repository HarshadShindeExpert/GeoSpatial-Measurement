from fastapi import APIRouter
from app.api.endpoints import files, measurements, health

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(files.router)
api_router.include_router(measurements.router)
