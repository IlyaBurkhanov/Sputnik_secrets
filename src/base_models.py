from enum import Enum
from pydantic import BaseModel, Field, root_validator
from fastapi import HTTPException


class LifeTime(Enum):
    sec = "sec"
    min = "min"
    hour = "hour"
    day = "day"
    week = "week"
    month = "month"
    year = "year"

    __measure: dict = {
        "sec": 1,
        "min": 60,
        "hour": 3600,
        "day": 3600 * 24,
        "week": 3600 * 24 * 7,
        "month": 3600 * 24 * 31,
        "year": 3600 * 24 * 365,
    }

    @classmethod
    def get_time(cls, measure: str):
        return cls.__measure[measure]


class SecretURL(BaseModel):
    secret_key: str


class Password(BaseModel):
    password: str = Field(description="Секретный пароль!")


class DecodeText(BaseModel):
    text: str = Field(description="Секретное сообщение")


class Generate(DecodeText, Password):
    life_time: int = Field(
        default=3600,
        description="Время жизни секрета. По умолчанию, час",
    )
    time_measure: LifeTime = Field(
        default=LifeTime.sec,
        description="Период времени",
    )

    @root_validator(pre=True)
    def check_life(cls, values):  # pylint: disable=E0213
        if bool(values.get("life_time")) != bool(values.get("time_measure")):
            raise HTTPException(
                status_code=422,
                detail="Set time_measure and life_time",
            )
        return values
