"""
FastAPI example: generate images with Mistral's Agents image_generation tool.

Run (from this directory):
    poetry install
    poetry run uvicorn app.main:app --reload --port 8000

Then:
    curl -X POST http://127.0.0.1:8000/generate \\
      -H 'Content-Type: application/json' \\
      -d '{"prompt": "An orange cat in an office"}'
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from functools import lru_cache
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import Settings, get_settings
from app.mistral_service import MistralImageService
from app.schemas import GenerateImageRequest, GenerateImageResponse, GeneratedImageInfo


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title="Mistral Image Generation Example",
    description=(
        "Minimal FastAPI service that creates images via Mistral's Agents API "
        "(`tools=[{'type': 'image_generation'}]`)."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

_settings = get_settings()
_settings.output_dir.mkdir(parents=True, exist_ok=True)
app.mount("/files", StaticFiles(directory=_settings.output_dir), name="files")


@lru_cache
def get_image_service() -> MistralImageService:
    return MistralImageService(get_settings())


@app.get("/health")
def health(settings: Settings = Depends(get_settings)) -> dict:
    return {
        "status": "ok",
        "use_mocks": settings.use_mocks,
        "model": settings.mistral_model,
    }


@app.post("/generate", response_model=GenerateImageResponse)
def generate_image(
    body: GenerateImageRequest,
    service: MistralImageService = Depends(get_image_service),
) -> GenerateImageResponse:
    """Generate an image from a text prompt using Mistral."""
    try:
        result = service.generate(body.prompt)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - passthrough for SDK/network errors
        raise HTTPException(
            status_code=502,
            detail=f"Mistral image generation failed: {exc}",
        ) from exc

    images = [
        GeneratedImageInfo(
            file_id=image.file_id,
            file_name=image.file_name,
            path=str(image.path),
            media_type=image.media_type,
            download_url=f"/files/{image.file_name}",
        )
        for image in result.images
    ]
    return GenerateImageResponse(
        prompt=result.prompt,
        message=result.message,
        images=images,
        conversation_id=result.conversation_id,
        agent_id=result.agent_id,
        mocked=result.mocked,
    )


@app.get("/images/{file_name}")
def get_image(
    file_name: str,
    settings: Settings = Depends(get_settings),
) -> FileResponse:
    """Serve a previously generated image by file name."""
    safe_name = Path(file_name).name
    path = settings.output_dir / safe_name
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Image not found")
    media_type = "image/jpeg" if path.suffix.lower() in {".jpg", ".jpeg"} else "image/png"
    return FileResponse(path, media_type=media_type, filename=safe_name)
