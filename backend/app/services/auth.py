from datetime import UTC, datetime

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError

from app.core.security import (
    create_access_token,
    create_confirmation_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import (
    AuthToken,
    LoginRequest,
    SignUpRequest,
    StoredUser,
    User,
)
from app.repositories.base import serialise_document
from app.services.email import EmailService


class EmailAlreadyRegisteredError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class EmailNotVerifiedError(Exception):
    pass


class InvalidConfirmationError(Exception):
    pass


class AuthService:
    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        self.users = database.users

    async def sign_up(self, payload: SignUpRequest) -> tuple[User, str]:
        now = datetime.now(UTC)
        document = {
            "display_name": payload.display_name,
            "email": str(payload.email),
            "password_hash": hash_password(payload.password),
            "email_verified": False,
            "email_verified_at": None,
            "created_at": now,
            "updated_at": now,
        }
        try:
            result = await self.users.insert_one(document)
        except DuplicateKeyError as error:
            raise EmailAlreadyRegisteredError from error
        document["_id"] = result.inserted_id
        stored = StoredUser.model_validate(serialise_document(document))
        token = create_confirmation_token(stored.id)
        try:
            confirmation_url = await EmailService().send_confirmation(
                str(stored.email), stored.display_name, token
            )
        except Exception:
            await self.users.delete_one({"_id": result.inserted_id})
            raise
        return User.model_validate(stored), confirmation_url

    async def confirm_email(self, token: str) -> User:
        try:
            payload = decode_token(token, "email_confirmation")
        except ValueError as error:
            raise InvalidConfirmationError from error
        user_id = payload["sub"]
        if not ObjectId.is_valid(user_id):
            raise InvalidConfirmationError
        now = datetime.now(UTC)
        document = await self.users.find_one_and_update(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "email_verified": True,
                    "email_verified_at": now,
                    "updated_at": now,
                }
            },
            return_document=True,
        )
        if document is None:
            raise InvalidConfirmationError
        return User.model_validate(serialise_document(document))

    async def resend_confirmation(self, email: str) -> str | None:
        document = await self.users.find_one({"email": email.lower()})
        if document is None or document.get("email_verified"):
            return None
        user = StoredUser.model_validate(serialise_document(document))
        token = create_confirmation_token(user.id)
        return await EmailService().send_confirmation(str(user.email), user.display_name, token)

    async def login(self, payload: LoginRequest) -> AuthToken:
        document = await self.users.find_one({"email": str(payload.email)})
        if document is None:
            raise InvalidCredentialsError
        user = StoredUser.model_validate(serialise_document(document))
        if not verify_password(payload.password, user.password_hash):
            raise InvalidCredentialsError
        if not user.email_verified:
            raise EmailNotVerifiedError
        public_user = User.model_validate(user)
        return AuthToken(access_token=create_access_token(user.id), user=public_user)

    async def get_user(self, user_id: str) -> User | None:
        if not ObjectId.is_valid(user_id):
            return None
        document = await self.users.find_one({"_id": ObjectId(user_id)})
        return User.model_validate(serialise_document(document)) if document else None
