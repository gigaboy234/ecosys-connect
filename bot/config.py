from typing import List

from pydantic import computed_field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    bot_token: str

    # PostgreSQL
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "ecosys"
    postgres_user: str = "ecosys"
    postgres_password: str = "secret"

    # Redis
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0

    admin_ids: List[int] = []

    @computed_field
    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @computed_field
    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "populate_by_name": True,
    }

    def model_post_init(self, __context) -> None:
        if isinstance(self.admin_ids, str):
            object.__setattr__(
                self,
                "admin_ids",
                [int(x.strip()) for x in self.admin_ids.split(",") if x.strip()],
            )


settings = Settings()
