from __future__ import annotations, absolute_import

import base64

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from slowapi.errors import RateLimitExceeded
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from config import async_session, engine, settings
from db import Base


def _get_fernet(salt: str, password: str) -> Fernet:
    password = bytes(password, "utf-8")
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=bytes(salt, "utf-8"),
        iterations=settings.ENCODE_ITERATORS,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password))
    return Fernet(key)


def decrypt_info(crypt_info: str, salt: str, password: str) -> str:
    decryption_key_fernet = _get_fernet(salt, password)
    return decryption_key_fernet.decrypt(bytes(crypt_info, "utf-8")).decode()


def encrypt_info(text: str, salt: str, password: str) -> str:
    encryption_key_fernet = _get_fernet(salt, password)
    return encryption_key_fernet.encrypt(bytes(text, "utf-8")).decode()


def get_encrypt_key(user_key: str) -> str:
    """Get encrypt key."""
    return encrypt_info(
        user_key,
        settings.SALT_KEY.get_secret_value(),
        settings.SECRET_KEY.get_secret_value(),
    )


def get_encrypt_text(user_text: str, user_key: str) -> str:
    """Get encrypt text."""
    return encrypt_info(
        user_text,
        settings.SALT_TEXT.get_secret_value(),
        user_key,
    )


def get_decrypt_text(crypt_text: str, user_key: str) -> str:
    text = decrypt_info(
        crypt_text,
        settings.SALT_TEXT.get_secret_value(),
        user_key,
    )
    return text


def get_decrypt_key(crypt_key: str) -> str:
    text = decrypt_info(
        crypt_key,
        settings.SALT_KEY.get_secret_value(),
        settings.SECRET_KEY.get_secret_value(),
    )
    return text


def limit_exceeded_handler(_: Request, exc: RateLimitExceeded) -> Response:
    return JSONResponse(
        {"error": f"Too Many Requests: {exc.detail}"}, status_code=429
    )


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session


async def init_models(drop: bool = False) -> None:
    async with engine.begin() as conn:
        if drop:
            await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
