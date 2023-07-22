from pydantic import BaseSettings, SecretStr, validator
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


class Settings(BaseSettings):
    # DB PARAMS
    DB_PORT: int
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: SecretStr
    HOST: str
    DSN: SecretStr = ""
    ECHO: bool
    POOL_SIZE: int = 10

    # SECRETS
    SALT_KEY: SecretStr
    SALT_TEXT: SecretStr
    SECRET_KEY: SecretStr
    ENCODE_ITERATORS: int = 2500

    # OTHER
    HOST_PORT: int = 8080
    IS_TEST: bool = False
    REQUEST_LIMIT: int = 600
    SERVICE_URL: str = "0.0.0.0"

    class Config:  # set env-file in docker-compose!
        env_file = ".local.env"

    @validator("DSN", pre=True, each_item=True, always=True)
    def create_dsn(cls, _, values):  # noqa: N805  # pylint: disable=C0321,E0213
        db_user = values["POSTGRES_USER"]
        db_password = values["POSTGRES_PASSWORD"]
        db_host = values["HOST"]
        db_schema = values["POSTGRES_DB"]
        value = f"postgresql+asyncpg://{db_user}:" \
                f"{db_password.get_secret_value()}@{db_host}/{db_schema}"
        return value


settings = Settings()

engine = create_async_engine(
    settings.DSN.get_secret_value(),
    pool_size=settings.POOL_SIZE,
    echo=settings.ECHO
)
async_session = async_sessionmaker(bind=engine, expire_on_commit=False)
