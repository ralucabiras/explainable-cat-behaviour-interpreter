from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.security import decode_token
from app.db.mongodb import get_database
from app.models.user import User
from app.services.auth import AuthService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
Database = Annotated[AsyncIOMotorDatabase, Depends(get_database)]


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    database: Database,
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token, "access")
    except ValueError:
        raise credentials_error from None
    user = await AuthService(database).get_user(payload["sub"])
    if user is None or not user.email_verified:
        raise credentials_error
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
