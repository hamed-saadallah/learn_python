"""Application settings loaded from environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Runtime configuration for the image generation API."""

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    mistral_api_key: str = ""
    mistral_model: str = "mistral-medium-latest"
    use_mocks: bool = True
    output_dir: Path = BASE_DIR / "output"
    agent_name: str = "Image Generation Agent"
    agent_instructions: str = (
        "Use the image generation tool whenever the user asks you to create an image. "
        "Keep any accompanying text short."
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    settings = Settings()
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    return settings
