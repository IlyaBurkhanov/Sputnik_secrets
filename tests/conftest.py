from dotenv import load_dotenv
load_dotenv("tests/.test.env")  # noqa

import asyncio
import pytest

from httpx import AsyncClient
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app import app as application
from config import async_session, engine
from db import Base


@pytest.fixture(scope='session', autouse=True)
async def prepare_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="session")
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(app=application, base_url="http://test") as ac:
        yield ac


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def async_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
