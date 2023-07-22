from uuid import uuid4

from sqlalchemy import DateTime, String, UUID
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, mapped_column


class Base(AsyncAttrs, DeclarativeBase):
    pass


class Secrets(Base):
    __tablename__ = "secrets"

    id = mapped_column(UUID, default=lambda: uuid4().hex, primary_key=True)
    key = mapped_column(String, nullable=False)
    message = mapped_column(String, nullable=False)
    dead_time = mapped_column(DateTime, nullable=False)
