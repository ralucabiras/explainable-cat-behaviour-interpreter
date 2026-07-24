from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import CurrentUser, Database
from app.models.pet import Pet, PetCreate, PetDeleteResponse, PetUpdate
from app.services.pets import DuplicatePetNameError, PetService

router = APIRouter()


@router.post("", response_model=Pet, status_code=status.HTTP_201_CREATED)
async def create_pet(payload: PetCreate, database: Database, current_user: CurrentUser) -> Pet:
    try:
        return await PetService(database).create(payload, current_user.id)
    except DuplicatePetNameError:
        raise HTTPException(
            status_code=409,
            detail="You already have a cat profile with this name",
        ) from None


@router.get("", response_model=list[Pet])
async def list_pets(database: Database, current_user: CurrentUser) -> list[Pet]:
    return await PetService(database).list(current_user.id)


@router.get("/{pet_id}", response_model=Pet)
async def get_pet(pet_id: str, database: Database, current_user: CurrentUser) -> Pet:
    pet = await PetService(database).get(pet_id, current_user.id)
    if pet is None:
        raise HTTPException(status_code=404, detail="Pet not found")
    return pet


@router.patch("/{pet_id}", response_model=Pet)
async def update_pet(
    pet_id: str,
    payload: PetUpdate,
    database: Database,
    current_user: CurrentUser,
) -> Pet:
    try:
        pet = await PetService(database).update(pet_id, payload, current_user.id)
    except DuplicatePetNameError:
        raise HTTPException(
            status_code=409,
            detail="You already have a cat profile with this name",
        ) from None
    if pet is None:
        raise HTTPException(status_code=404, detail="Pet not found")
    return pet


@router.delete("/{pet_id}", response_model=PetDeleteResponse)
async def delete_pet(
    pet_id: str,
    database: Database,
    current_user: CurrentUser,
) -> PetDeleteResponse:
    result = await PetService(database).delete(pet_id, current_user.id)
    if result is None:
        raise HTTPException(status_code=404, detail="Pet not found")
    return result
