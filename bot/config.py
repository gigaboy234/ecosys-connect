from typing import List

from pydantic import computed_field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    vk_token: str           # токен группы ВКонтакте
    vk_group_id: int = 0    # ID группы (опционально, для проверки)

    # PostgreSQL
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "ecosys"
    postgres_user: str = "ecosys"
    postgres_password: str = "secret"

    admin_vk_ids: List[int] = []

    @computed_field
    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "populate_by_name": True,
    }

    def model_post_init(self, __context) -> None:
        if isinstance(self.admin_vk_ids, str):
            object.__setattr__(
                self,
                "admin_vk_ids",
                [int(x.strip()) for x in self.admin_vk_ids.split(",") if x.strip()],
            )


settings = Settings()
