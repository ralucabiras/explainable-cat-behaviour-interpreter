from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.mongodb import get_database
from app.models.pet import Pet, PetCreate
from app.services.pets import PetService

router = APIRouter()
Database = Annotated[AsyncIOMotorDatabase, Depends(get_database)]


@router.post("", response_model=Pet, status_code=status.HTTP_201_CREATED)
async def create_pet(payload: PetCreate, database: Database) -> Pet:
    return await PetService(database).create(payload)


@router.get("", response_model=list[Pet])
async def list_pets(database: Database) -> list[Pet]:
    return await PetService(database).list()


@router.get("/{pet_id}", response_model=Pet)
async def get_pet(pet_id: str, database: Database) -> Pet:
    pet = await PetService(database).get(pet_id)
    if pet is None:
        raise HTTPException(status_code=404, detail="Pet not found")
    return pet

