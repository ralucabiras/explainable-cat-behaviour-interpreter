from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from app.api.dependencies import CurrentUser, Database
from app.models.observation import Observation, ObservationCreate
from app.services.observations import ObservationService

router = APIRouter()


@router.post("", response_model=Observation, status_code=status.HTTP_201_CREATED)
async def create_observation(
    payload: ObservationCreate, database: Database, current_user: CurrentUser
) -> Observation:
    observation = await ObservationService(database).create(payload, current_user.id)
    if observation is None:
        raise HTTPException(status_code=404, detail="Pet not found")
    return observation


@router.get("", response_model=list[Observation])
async def list_observations(
    database: Database,
    current_user: CurrentUser,
    pet_id: Annotated[str | None, Query()] = None,
) -> list[Observation]:
    return await ObservationService(database).list(current_user.id, pet_id)


@router.get("/{observation_id}", response_model=Observation)
async def get_observation(
    observation_id: str, database: Database, current_user: CurrentUser
) -> Observation:
    observation = await ObservationService(database).get(observation_id, current_user.id)
    if observation is None:
        raise HTTPException(status_code=404, detail="Observation not found")
    return observation
