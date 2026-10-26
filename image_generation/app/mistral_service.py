"""Mistral Agents image_generation integration."""

from __future__ import annotations

import base64
import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.config import Settings, get_settings


@dataclass
class GeneratedImage:
    """One generated image written to disk."""

    file_id: str
    file_name: str
    path: Path
    media_type: str = "image/png"


@dataclass
class GenerationResult:
    """Result of an image generation request."""

    prompt: str
    message: str
    images: list[GeneratedImage]
    conversation_id: str | None = None
    agent_id: str | None = None
    mocked: bool = False


# Minimal 1x1 PNG used by mock mode so the API can be exercised offline.
_MOCK_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


def _safe_slug(value: str, max_length: int = 40) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return (slug or "image")[:max_length]


def _is_tool_file_chunk(chunk: Any) -> bool:
    """Return True if chunk looks like a Mistral ToolFileChunk / tool_file."""
    chunk_type = getattr(chunk, "type", None)
    if chunk_type in {"tool_file", "tool.file"}:
        return True
    if hasattr(chunk, "file_id") and getattr(chunk, "tool", None) == "image_generation":
        return True
    try:
        from mistralai.client.models import ToolFileChunk

        return isinstance(chunk, ToolFileChunk)
    except Exception:
        return False


def _extract_text(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    parts: list[str] = []
    if isinstance(content, list):
        for chunk in content:
            text = getattr(chunk, "text", None)
            if text:
                parts.append(text)
            elif isinstance(chunk, str):
                parts.append(chunk)
            elif isinstance(chunk, dict) and chunk.get("type") == "text":
                parts.append(str(chunk.get("text", "")))
    return "\n".join(parts).strip()


class MistralImageService:
    """Create images via Mistral's Agents image_generation tool."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._client: Any | None = None
        self._agent_id: str | None = None

    @property
    def client(self) -> Any:
        if self._client is None:
            if not self.settings.mistral_api_key:
                raise RuntimeError(
                    "MISTRAL_API_KEY is required when USE_MOCKS=false. "
                    "Copy .env.example to .env and set your key."
                )
            from mistralai.client import Mistral

            self._client = Mistral(api_key=self.settings.mistral_api_key)
        return self._client

    def get_or_create_agent(self) -> str:
        """Create (once) an agent with the image_generation tool enabled."""
        if self._agent_id:
            return self._agent_id

        agent = self.client.beta.agents.create(
            model=self.settings.mistral_model,
            name=self.settings.agent_name,
            description="Agent used to generate images from text prompts.",
            instructions=self.settings.agent_instructions,
            tools=[{"type": "image_generation"}],
            completion_args={
                "temperature": 0.3,
                "top_p": 0.95,
            },
        )
        self._agent_id = agent.id
        return self._agent_id

    def generate(self, prompt: str) -> GenerationResult:
        """Generate one or more images for the given prompt."""
        cleaned = prompt.strip()
        if not cleaned:
            raise ValueError("prompt must not be empty")

        if self.settings.use_mocks:
            return self._generate_mock(cleaned)

        agent_id = self.get_or_create_agent()
        response = self.client.beta.conversations.start(
            agent_id=agent_id,
            inputs=cleaned,
        )
        return self._materialize_response(cleaned, response, agent_id=agent_id)

    def _generate_mock(self, prompt: str) -> GenerationResult:
        request_id = uuid.uuid4().hex[:8]
        file_name = f"mock-{_safe_slug(prompt)}-{request_id}.png"
        path = self.settings.output_dir / file_name
        path.write_bytes(_MOCK_PNG)
        return GenerationResult(
            prompt=prompt,
            message="[mock] Generated a placeholder PNG for local development.",
            images=[
                GeneratedImage(
                    file_id=f"mock-file-{request_id}",
                    file_name=file_name,
                    path=path,
                )
            ],
            conversation_id=f"mock-conversation-{request_id}",
            agent_id="mock-agent",
            mocked=True,
        )

    def _materialize_response(
        self,
        prompt: str,
        response: Any,
        *,
        agent_id: str,
    ) -> GenerationResult:
        images: list[GeneratedImage] = []
        message = ""
        outputs = getattr(response, "outputs", None) or []

        for entry in outputs:
            entry_type = getattr(entry, "type", None)
            content = getattr(entry, "content", None)
            if entry_type == "message.output":
                text = _extract_text(content)
                if text:
                    message = text
                if isinstance(content, list):
                    for index, chunk in enumerate(content):
                        if not _is_tool_file_chunk(chunk):
                            continue
                        images.append(self._download_chunk(chunk, prompt, index))
            elif isinstance(content, list):
                for index, chunk in enumerate(content):
                    if _is_tool_file_chunk(chunk):
                        images.append(self._download_chunk(chunk, prompt, index))

        if not images:
            raise RuntimeError(
                "Mistral returned no generated image files. "
                "Check that the agent has the image_generation tool and your account has access."
            )

        return GenerationResult(
            prompt=prompt,
            message=message or "Image generated successfully.",
            images=images,
            conversation_id=getattr(response, "conversation_id", None),
            agent_id=agent_id,
            mocked=False,
        )

    def _download_chunk(self, chunk: Any, prompt: str, index: int) -> GeneratedImage:
        file_id = getattr(chunk, "file_id", None)
        if not file_id and isinstance(chunk, dict):
            file_id = chunk.get("file_id")
        if not file_id:
            raise RuntimeError("Image chunk is missing file_id")

        raw_name = getattr(chunk, "file_name", None) or f"{_safe_slug(prompt)}-{index}.png"
        file_type = getattr(chunk, "file_type", None) or "png"
        if not str(raw_name).lower().endswith(f".{file_type}"):
            raw_name = f"{raw_name}.{file_type}"

        unique_name = f"{Path(raw_name).stem}-{uuid.uuid4().hex[:8]}.{file_type}"
        path = self.settings.output_dir / unique_name

        file_bytes = self.client.files.download(file_id=file_id).read()
        path.write_bytes(file_bytes)

        media_type = "image/jpeg" if file_type in {"jpg", "jpeg"} else f"image/{file_type}"
        return GeneratedImage(
            file_id=file_id,
            file_name=unique_name,
            path=path,
            media_type=media_type,
        )
