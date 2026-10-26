import os
from dotenv import load_dotenv
from pydantic import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    # Mistral AI Configuration
    mistral_api_key: str = os.getenv("MISTRAL_API_KEY", "")
    mistral_model: str = "mistral-medium"
    mistral_temperature: float = 0.7
    mistral_max_tokens: int = 1024

    # Weaviate Configuration
    weaviate_host: str = os.getenv("WEAVIATE_HOST", "localhost")
    weaviate_port: int = int(os.getenv("WEAVIATE_PORT", "8080"))
    weaviate_scheme: str = os.getenv("WEAVIATE_SCHEME", "http")

    # Application Configuration
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))

    # RAG Configuration
    rag_top_k: int = 3
    rag_similarity_threshold: float = 0.7

    class Config:
        case_sensitive = False

    @property
    def weaviate_url(self) -> str:
        return f"{self.weaviate_scheme}://{self.weaviate_host}:{self.weaviate_port}"


settings = Settings()
