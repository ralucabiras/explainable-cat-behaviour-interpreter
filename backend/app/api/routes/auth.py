from typing import Annotated

from fastapi import APIRouter, Body, HTTPException, Query, status
from pydantic import EmailStr

from app.api.dependencies import CurrentUser, Database
from app.core.config import get_settings
from app.models.user import (
    AuthToken,
    LoginRequest,
    MessageResponse,
    SignUpRequest,
    SignUpResponse,
    User,
)
from app.services.auth import (
    AuthService,
    EmailAlreadyRegisteredError,
    EmailNotVerifiedError,
    InvalidConfirmationError,
    InvalidCredentialsError,
)

router = APIRouter()


@router.post("/signup", response_model=SignUpResponse, status_code=status.HTTP_201_CREATED)
async def sign_up(payload: SignUpRequest, database: Database) -> SignUpResponse:
    try:
        user, confirmation_url = await AuthService(database).sign_up(payload)
    except EmailAlreadyRegisteredError:
        raise HTTPException(
            status_code=409, detail="An account with this email already exists"
        ) from None
    except RuntimeError as error:
        raise HTTPException(
            status_code=503, detail="Confirmation email could not be sent"
        ) from error
    development_url = confirmation_url if get_settings().email_delivery_mode == "console" else None
    return SignUpResponse(
        message="Account created. Check your email to confirm it.",
        email=user.email,
        development_confirmation_url=development_url,
    )


@router.get("/confirm-email", response_model=MessageResponse)
async def confirm_email(
    database: Database,
    token: Annotated[str, Query(min_length=1)],
) -> MessageResponse:
    try:
        await AuthService(database).confirm_email(token)
    except InvalidConfirmationError:
        raise HTTPException(
            status_code=400, detail="Confirmation link is invalid or expired"
        ) from None
    return MessageResponse(message="Email confirmed. You can now log in.")


@router.post("/resend-confirmation", response_model=MessageResponse)
async def resend_confirmation(
    database: Database,
    email: Annotated[EmailStr, Body(embed=True)],
) -> MessageResponse:
    try:
        await AuthService(database).resend_confirmation(str(email))
    except RuntimeError as error:
        raise HTTPException(
            status_code=503, detail="Confirmation email could not be sent"
        ) from error
    return MessageResponse(
        message="If an unconfirmed account exists, a new confirmation email has been sent."
    )


@router.post("/login", response_model=AuthToken)
async def login(payload: LoginRequest, database: Database) -> AuthToken:
    try:
        return await AuthService(database).login(payload)
    except InvalidCredentialsError:
        raise HTTPException(status_code=401, detail="Incorrect email or password") from None
    except EmailNotVerifiedError:
        raise HTTPException(
            status_code=403, detail="Confirm your email before logging in"
        ) from None


@router.get("/me", response_model=User)
async def me(current_user: CurrentUser) -> User:
    return current_user
