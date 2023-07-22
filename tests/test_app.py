import asyncio
import pytest
from httpx import AsyncClient
from sqlalchemy.future import select
from db import Secrets
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.parametrize(
    "password, text, life_time, time_measure, status_code",
    [
        ("qwerty", "qwerty", 60, "sec", 201),
        (None, "qwerty", 60, "sec", 422),
        ("qwerty", None, 60, "sec", 422),
        ("qwerty", "Какой-то текст на русском", 60, "sec", 201),
        ("qwerty", "qwerty", 60, None, 422),
        ("qwerty", "qwerty", None, "sec", 422),
        ("qwerty", "qwerty", None, None, 201),
    ],
)
async def test_create_secret(password, text, life_time, time_measure, status_code, async_client: AsyncClient):
    data = {
        key: value for key, value in
        zip(["password", "text", "life_time", "time_measure"], [password, text, life_time, time_measure])
        if value
    }
    response = await async_client.post("/generate", json=data)
    assert response.status_code == status_code


async def test_get_secret(async_client: AsyncClient):
    our_text = "BLA BLA BLA 1234 АВСДЕЁ"
    data = {
        "password": "long_password",
        "text": our_text,
    }
    response = await async_client.post("/generate", json=data)
    assert response.status_code == 201
    result = response.json()

    key = result.get("secret_key")
    assert key is not None

    data = {"password": "long_password"}

    bad_key = "1111"
    response = await async_client.post(f"/secrets/{bad_key}", json=data)
    assert response.status_code == 422

    unknown_secret = "1" * 32
    response = await async_client.post(f"/secrets/{unknown_secret}", json=data)
    assert response.status_code == 404

    # without password
    response = await async_client.post(f"/secrets/{key}", json={})
    assert response.status_code == 422

    # uncorrect password
    response = await async_client.post(f"/secrets/{key}", json={"password": "BAD PASSWORD"})
    assert response.status_code == 403

    # correct password
    response = await async_client.post(f"/secrets/{key}", json=data)
    assert response.status_code == 200
    result = response.json()
    text = result.get("text")
    assert text is not None
    assert text == our_text

    # add response
    response = await async_client.post(f"/secrets/{key}", json=data)
    assert response.status_code == 404


async def test_crypto(async_client: AsyncClient, async_db: AsyncSession):
    our_text = "QWERty123"
    our_password = "123qwer"
    data = {
        "password": our_password,
        "text": our_text,
    }
    response = await async_client.post("/generate", json=data)
    assert response.status_code == 201
    result = response.json()
    key: str = result.get("secret_key")
    assert key is not None

    secret_data = await async_db.execute(select(Secrets).where(Secrets.id == key))
    secret = secret_data.scalar()
    assert secret is not None
    assert secret.key != our_password
    assert secret.message != our_text


async def test_lifetime(async_client: AsyncClient):
    data = {"password": "qwer", "text": "qwer"}
    data1 = data | {"life_time": 1, "time_measure": "sec"}
    data2 = data | {"life_time": 5, "time_measure": "min"}

    response = await async_client.post("/generate", json=data1)
    key1: str = response.json().get("secret_key")

    response = await async_client.post("/generate", json=data2)
    key2: str = response.json().get("secret_key")

    await asyncio.sleep(2)

    # Dead message
    response = await async_client.post(f"/secrets/{key1}", json=data)
    assert response.status_code == 403

    # Live message
    response = await async_client.post(f"/secrets/{key2}", json=data)
    assert response.status_code == 200

    # Drop message
    response = await async_client.post(f"/secrets/{key1}", json=data)
    assert response.status_code == 404


async def test_concurrency(async_client: AsyncClient, async_db: AsyncSession):
    data = {"password": "qwer", "text": "qwer"}
    response = await async_client.post("/generate", json=data)
    key: str = response.json().get("secret_key")

    async def get_secret_with_sleep(sleep_time: float, use_key: str) -> int:
        await asyncio.sleep(sleep_time)
        result = await async_client.post(f"/secrets/{use_key}", json=data)
        return result.status_code

    async def concurrent_request(sleep_time: float, use_key: str) -> bool | None:
        await asyncio.sleep(sleep_time)
        result = await async_db.execute(select(Secrets).where(Secrets.id == use_key).with_for_update())
        await asyncio.sleep(0.3)
        if not (secret := result.scalar()):
            return True
        await async_db.delete(secret)
        await async_db.commit()

    # wait drop!
    concurrent_status, db_status = await asyncio.gather(
        get_secret_with_sleep(0.3, key),
        concurrent_request(.0, key),
    )
    assert concurrent_status == 404
    assert db_status is None

    response = await async_client.post("/generate", json=data)
    key: str = response.json().get("secret_key")

    # first read!
    concurrent_status, db_status = await asyncio.gather(
        get_secret_with_sleep(0, key),
        concurrent_request(.3, key),
    )
    assert concurrent_status == 200
    assert db_status
