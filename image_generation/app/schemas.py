"""Pydantic request/response models."""

from pydantic import BaseModel, Field, field_validator


class GenerateImageRequest(BaseModel):
    """Body for POST /generate."""

    prompt: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        examples=["An orange cat sitting at a desk in a sunny office"],
        description="Text description of the image to generate.",
    )

    @field_validator("prompt")
    @classmethod
    def prompt_must_not_be_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("prompt must not be empty")
        return cleaned


class GeneratedImageInfo(BaseModel):
    """Metadata for one saved image."""

    file_id: str
    file_name: str
    path: str
    media_type: str
    download_url: str


class GenerateImageResponse(BaseModel):
    """Response returned by POST /generate."""

    prompt: str
    message: str
    images: list[GeneratedImageInfo]
    conversation_id: str | None = None
    agent_id: str | None = None
    mocked: bool = False
