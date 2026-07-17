from functools import lru_cache
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4.1-mini", alias="OPENAI_MODEL")
    database_path: Path = Field(default=Path("./monday_api_lab.db"), alias="DATABASE_PATH")
    call_model_on_touch: bool = Field(default=False, alias="CALL_MODEL_ON_TOUCH")
    persona_path: Path = Path("memory/persona.md")
    stable_memory_path: Path = Path("memory/stable_memory.md")
    recent_message_limit: int = 12

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore", populate_by_name=True)

    @property
    def has_openai_api_key(self) -> bool:
        return bool(self.openai_api_key and self.openai_api_key.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()
