"""Unit tests for MistralImageService response parsing."""

from __future__ import annotations

from types import SimpleNamespace
from pathlib import Path

import pytest

from app.config import Settings
from app.mistral_service import MistralImageService


class _FakeDownload:
    def read(self) -> bytes:
        return b"\x89PNG\r\n\x1a\nfake-image"


class _FakeFiles:
    def download(self, file_id: str) -> _FakeDownload:
        assert file_id == "file-123"
        return _FakeDownload()


class _FakeClient:
    def __init__(self) -> None:
        self.files = _FakeFiles()
        self.beta = SimpleNamespace(
            agents=SimpleNamespace(create=self._create_agent),
            conversations=SimpleNamespace(start=self._start),
        )

    def _create_agent(self, **_: object) -> SimpleNamespace:
        return SimpleNamespace(id="agent-abc")

    def _start(self, **_: object) -> SimpleNamespace:
        chunk = SimpleNamespace(
            type="tool_file",
            tool="image_generation",
            file_id="file-123",
            file_name="cat",
            file_type="png",
        )
        text = SimpleNamespace(type="text", text="Here is your orange cat.")
        message = SimpleNamespace(type="message.output", content=[text, chunk])
        return SimpleNamespace(outputs=[message], conversation_id="conv-1")


def test_generate_downloads_tool_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    settings = Settings(
        mistral_api_key="test-key",
        use_mocks=False,
        output_dir=tmp_path,
        mistral_model="mistral-medium-latest",
    )
    service = MistralImageService(settings)
    fake = _FakeClient()
    monkeypatch.setattr(service, "_client", fake)

    result = service.generate("orange cat")

    assert result.mocked is False
    assert result.agent_id == "agent-abc"
    assert result.conversation_id == "conv-1"
    assert result.message == "Here is your orange cat."
    assert len(result.images) == 1
    assert result.images[0].file_id == "file-123"
    assert result.images[0].path.is_file()
    assert result.images[0].path.read_bytes().startswith(b"\x89PNG")


def test_generate_requires_api_key_when_not_mocked(tmp_path: Path) -> None:
    settings = Settings(
        mistral_api_key="",
        use_mocks=False,
        output_dir=tmp_path,
    )
    service = MistralImageService(settings)
    with pytest.raises(RuntimeError, match="MISTRAL_API_KEY"):
        _ = service.client
