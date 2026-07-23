from datetime import datetime

from pydantic import EmailStr, Field, field_validator

from app.models.common import APIModel, StoredModel


class SignUpRequest(APIModel):
    display_name: str = Field(min_length=2, max_length=80)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("display_name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        return " ".join(value.split())

    @field_validator("email")
    @classmethod
    def normalise_email(cls, value: EmailStr) -> str:
        return str(value).lower()


class LoginRequest(APIModel):
    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def normalise_email(cls, value: EmailStr) -> str:
        return str(value).lower()


class User(StoredModel):
    display_name: str
    email: EmailStr
    email_verified: bool = False
    email_verified_at: datetime | None = None


class StoredUser(User):
    password_hash: str


class AuthToken(APIModel):
    access_token: str
    token_type: str = "bearer"
    user: User


class SignUpResponse(APIModel):
    message: str
    email: EmailStr
    development_confirmation_url: str | None = None


class MessageResponse(APIModel):
    message: str
