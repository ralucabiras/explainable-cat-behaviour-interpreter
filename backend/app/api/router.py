from fastapi import APIRouter

from app.api.routes import health, observations, pets

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(pets.router, prefix="/pets", tags=["pets"])
api_router.include_router(observations.router, prefix="/observations", tags=["observations"])

