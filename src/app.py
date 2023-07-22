from datetime import datetime, timedelta

from fastapi import Depends, FastAPI, HTTPException
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from base_models import DecodeText, Generate, LifeTime, Password, SecretURL
from config import settings
from db import Secrets
from utils import (
    get_decrypt_text,
    get_decrypt_key,
    get_encrypt_key,
    get_encrypt_text,
    get_session,
    init_models,
    limit_exceeded_handler,
)

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.add_exception_handler(RateLimitExceeded, limit_exceeded_handler)


@app.on_event("startup")
async def startup_event():
    await init_models(settings.IS_TEST)


@app.post(
    "/generate",
    status_code=201,
    description="Сохранение секретного послания",
    tags=["Secrets"],
)
@limiter.limit(f"{settings.REQUEST_LIMIT}/minute")
async def generate(
        request: Request,  # pylint: disable=W0613
        data: Generate,
        db: AsyncSession = Depends(get_session),  # noqa: B008
) -> SecretURL:
    encrypt_key = get_encrypt_key(data.password)
    encrypt_text = get_encrypt_text(data.text, data.password)
    dead_time = datetime.utcnow() + timedelta(
        seconds=LifeTime.get_time(data.time_measure.name) * data.life_time,
    )
    record = Secrets(
        key=encrypt_key,
        message=encrypt_text,
        dead_time=dead_time,
    )
    db.add(record)
    await db.commit()
    return SecretURL(secret_key=record.id)


@app.post(
    "/secrets/{secret_key}",
    description="Получение секретного послания",
    tags=["Secrets"],
)
@limiter.limit(f"{settings.REQUEST_LIMIT}/minute")
async def get_secret(
        request: Request,  # pylint: disable=W0613
        secret_key: str,
        password: Password,
        db: AsyncSession = Depends(get_session),  # noqa: B008
) -> DecodeText:
    if not 31 < len(secret_key) < 37:
        raise HTTPException(status_code=422, detail="Uncorrected secret key")

    # transaction locker
    value = await db.execute(
        select(Secrets).where(Secrets.id == secret_key).with_for_update()
    )
    if (secret := value.scalar()) is None:
        raise HTTPException(status_code=404, detail="Secret not found")

    if password.password != get_decrypt_key(secret.key):
        raise HTTPException(status_code=403, detail="Wrong password")

    try:
        if datetime.utcnow() > secret.dead_time:
            raise HTTPException(
                status_code=403,
                detail="The life of the secret has expired",
            )
        text = get_decrypt_text(secret.message, password.password)
        return DecodeText(text=text)
    finally:
        await db.delete(secret)
        await db.commit()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host=settings.SERVICE_URL,
        port=settings.HOST_PORT,
        reload=True,
    )
