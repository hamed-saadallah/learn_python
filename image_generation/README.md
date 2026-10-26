# Mistral Image Generation (FastAPI)

Minimal Python example that exposes a FastAPI endpoint and generates images through
[Mistral's Agents `image_generation` tool](https://docs.mistral.ai/agents/connectors/image_generation)
(powered by Black Forest Labs FLUX).

## How it works

1. Create a Mistral agent with `tools=[{"type": "image_generation"}]`.
2. Start a conversation with your text prompt.
3. Download each `tool_file` chunk via `client.files.download(file_id=...)`.
4. Save the PNG under `output/` and return download URLs.

Mock mode is on by default so you can run and test without an API key.

## Setup

```bash
cd image_generation
cp .env.example .env
poetry install
```

### Mock mode (default)

```bash
poetry run uvicorn app.main:app --reload --port 8000
```

### Live Mistral API

Edit `.env`:

```env
USE_MOCKS=false
MISTRAL_API_KEY=sk-...
MISTRAL_MODEL=mistral-medium-latest
```

Then start the server the same way. Image generation requires a Mistral account with
access to the Agents image generation connector.

## API

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Liveness + mock/model config |
| `POST` | `/generate` | Generate an image from `{ "prompt": "..." }` |
| `GET` | `/files/{name}` | Static file for a saved image |
| `GET` | `/images/{name}` | Same image via `FileResponse` |
| `GET` | `/docs` | Interactive Swagger UI |

### Example request

```bash
curl -s -X POST http://127.0.0.1:8000/generate \
  -H 'Content-Type: application/json' \
  -d '{"prompt": "An orange cat sitting at a desk in a sunny office"}' | jq
```

Example response (mock):

```json
{
  "prompt": "An orange cat sitting at a desk in a sunny office",
  "message": "[mock] Generated a placeholder PNG for local development.",
  "images": [
    {
      "file_id": "mock-file-...",
      "file_name": "mock-an-orange-cat-....png",
      "path": ".../output/mock-an-orange-cat-....png",
      "media_type": "image/png",
      "download_url": "/files/mock-an-orange-cat-....png"
    }
  ],
  "conversation_id": "mock-conversation-...",
  "agent_id": "mock-agent",
  "mocked": true
}
```

## Tests

```bash
poetry run pytest -q
```

## Project layout

```
image_generation/
├── app/
│   ├── main.py              # FastAPI routes
│   ├── mistral_service.py   # Agents + file download
│   ├── config.py
│   └── schemas.py
├── output/                  # Saved PNGs
├── tests/
├── .env.example
└── pyproject.toml
```
