from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from jwt import InvalidTokenError
from pwdlib import PasswordHash

from app.core.config import get_settings

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, encoded: str) -> bool:
    return password_hash.verify(password, encoded)


def create_token(subject: str, token_type: str, lifetime: timedelta) -> str:
    now = datetime.now(UTC)
    payload = {"sub": subject, "type": token_type, "iat": now, "exp": now + lifetime}
    return jwt.encode(payload, get_settings().jwt_secret, algorithm="HS256")


def decode_token(token: str, expected_type: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, get_settings().jwt_secret, algorithms=["HS256"])
    except InvalidTokenError as error:
        raise ValueError("Invalid or expired token") from error
    if payload.get("type") != expected_type or not payload.get("sub"):
        raise ValueError("Invalid token purpose")
    return payload


def create_access_token(user_id: str) -> str:
    return create_token(
        user_id,
        "access",
        timedelta(minutes=get_settings().access_token_minutes),
    )


def create_confirmation_token(user_id: str) -> str:
    return create_token(
        user_id,
        "email_confirmation",
        timedelta(hours=get_settings().confirmation_token_hours),
    )
