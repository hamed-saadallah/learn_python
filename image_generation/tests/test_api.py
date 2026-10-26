"""API tests using mock mode (no Mistral API key required)."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import app, get_image_service
from app.mistral_service import MistralImageService


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    settings = Settings(
        mistral_api_key="",
        use_mocks=True,
        output_dir=tmp_path / "output",
        mistral_model="mistral-medium-latest",
    )
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    service = MistralImageService(settings)

    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_image_service] = lambda: service
    monkeypatch.setenv("USE_MOCKS", "true")

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["use_mocks"] is True


def test_generate_returns_mock_image(client: TestClient, tmp_path: Path) -> None:
    response = client.post(
        "/generate",
        json={"prompt": "An orange cat in an office"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["mocked"] is True
    assert payload["prompt"] == "An orange cat in an office"
    assert len(payload["images"]) == 1

    image = payload["images"][0]
    saved = Path(image["path"])
    assert saved.is_file()
    assert saved.stat().st_size > 0
    assert image["download_url"].startswith("/files/")


def test_generate_rejects_empty_prompt(client: TestClient) -> None:
    response = client.post("/generate", json={"prompt": "   "})
    assert response.status_code == 422


def test_get_image_by_name(client: TestClient) -> None:
    created = client.post("/generate", json={"prompt": "blue mountain lake"}).json()
    file_name = created["images"][0]["file_name"]

    response = client.get(f"/images/{file_name}")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/")
    assert response.content.startswith(b"\x89PNG")
