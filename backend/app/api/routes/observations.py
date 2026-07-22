from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.mongodb import get_database
from app.models.observation import Observation, ObservationCreate
from app.services.observations import ObservationService

router = APIRouter()
Database = Annotated[AsyncIOMotorDatabase, Depends(get_database)]


@router.post("", response_model=Observation, status_code=status.HTTP_201_CREATED)
async def create_observation(payload: ObservationCreate, database: Database) -> Observation:
    observation = await ObservationService(database).create(payload)
    if observation is None:
        raise HTTPException(status_code=404, detail="Pet not found")
    return observation


@router.get("", response_model=list[Observation])
async def list_observations(
    database: Database, pet_id: Annotated[str | None, Query()] = None
) -> list[Observation]:
    return await ObservationService(database).list(pet_id)


@router.get("/{observation_id}", response_model=Observation)
async def get_observation(observation_id: str, database: Database) -> Observation:
    observation = await ObservationService(database).get(observation_id)
    if observation is None:
        raise HTTPException(status_code=404, detail="Observation not found")
    return observation

