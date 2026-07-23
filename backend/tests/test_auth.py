from copy import deepcopy

import pytest
from bson import ObjectId

from app.core.security import decode_token
from app.models.user import LoginRequest, SignUpRequest
from app.services.auth import (
    AuthService,
    EmailNotVerifiedError,
    InvalidCredentialsError,
)


class InsertResult:
    def __init__(self, inserted_id: ObjectId) -> None:
        self.inserted_id = inserted_id


class DeleteResult:
    deleted_count = 1


class FakeUsers:
    def __init__(self) -> None:
        self.documents: list[dict] = []

    async def insert_one(self, document: dict) -> InsertResult:
        stored = deepcopy(document)
        stored["_id"] = ObjectId()
        self.documents.append(stored)
        return InsertResult(stored["_id"])

    async def find_one(self, query: dict) -> dict | None:
        return next(
            (
                deepcopy(document)
                for document in self.documents
                if all(document.get(key) == value for key, value in query.items())
            ),
            None,
        )

    async def find_one_and_update(
        self, query: dict, update: dict, return_document: bool
    ) -> dict | None:
        del return_document
        for document in self.documents:
            if all(document.get(key) == value for key, value in query.items()):
                document.update(update["$set"])
                return deepcopy(document)
        return None

    async def delete_one(self, query: dict) -> DeleteResult:
        self.documents = [
            document
            for document in self.documents
            if not all(document.get(key) == value for key, value in query.items())
        ]
        return DeleteResult()


class FakeDatabase:
    def __init__(self) -> None:
        self.users = FakeUsers()


async def test_signup_confirmation_and_login(monkeypatch) -> None:
    database = FakeDatabase()

    async def capture_email(_self, _email: str, _name: str, token: str) -> str:
        return f"http://localhost:5173/confirm-email?token={token}"

    monkeypatch.setattr("app.services.auth.EmailService.send_confirmation", capture_email)
    service = AuthService(database)
    user, url = await service.sign_up(
        SignUpRequest(
            display_name="Cat Owner",
            email="OWNER@EXAMPLE.COM",
            password="correct-horse",
        )
    )

    assert user.email == "owner@example.com"
    assert user.email_verified is False
    assert database.users.documents[0]["password_hash"] != "correct-horse"
    with pytest.raises(EmailNotVerifiedError):
        await service.login(LoginRequest(email="owner@example.com", password="correct-horse"))

    confirmation_token = url.split("token=", 1)[1]
    confirmed = await service.confirm_email(confirmation_token)
    assert confirmed.email_verified is True
    auth = await service.login(LoginRequest(email="owner@example.com", password="correct-horse"))
    assert decode_token(auth.access_token, "access")["sub"] == user.id
    assert auth.user.email == user.email


async def test_login_rejects_wrong_password() -> None:
    with pytest.raises(InvalidCredentialsError):
        await AuthService(FakeDatabase()).login(
            LoginRequest(email="nobody@example.com", password="wrong-password")
        )


async def test_failed_email_delivery_rolls_back_account(monkeypatch) -> None:
    database = FakeDatabase()

    async def fail_email(*_args) -> str:
        raise RuntimeError("SMTP unavailable")

    monkeypatch.setattr("app.services.auth.EmailService.send_confirmation", fail_email)
    with pytest.raises(RuntimeError, match="SMTP unavailable"):
        await AuthService(database).sign_up(
            SignUpRequest(
                display_name="Cat Owner",
                email="owner@example.com",
                password="correct-horse",
            )
        )
    assert database.users.documents == []
