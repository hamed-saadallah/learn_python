# RAG

A simple **RAG-style PDF summarization agent** built with:

- **[CrewAI](https://docs.crewai.com/)** for agent orchestration
- **[Mistral AI](https://mistral.ai/)** as the LLM provider (via CrewAI / LiteLLM)
- **Mocked PDF extraction and LLM calls** for local development without API keys

## Project layout

```text
RAG/
├── main.py                     # CLI entry point
├── rag_crew/
│   ├── crew.py                 # Crew assembly (@CrewBase)
│   ├── config/
│   │   ├── agents.yaml         # CrewAI agent definitions
│   │   └── tasks.yaml          # CrewAI task definitions
│   └── tools/
│       └── pdf_reader.py       # CrewAI tool for PDF text extraction
├── services/
│   ├── pdf_service.py          # PDF loading (mock + real pypdf path)
│   └── llm_factory.py          # Mistral / mock LLM selection
├── llm/
│   └── mock_mistral_llm.py     # Mock Mistral LLM for local dev
├── data/
│   ├── mock_pdf_content.txt    # Stand-in PDF text used in mock mode
│   └── documents/
│       └── sample_report.pdf   # Placeholder path for demos
├── output/                     # Generated summaries
└── tests/
    └── test_rag_skeleton.py
```

## Quick start (mock mode)

```bash
cd RAG
cp .env.example .env
pip install -e ".[dev]"   # or: pip install crewai crewai-tools python-dotenv pypdf pytest
python main.py
```

By default `USE_MOCKS=true`:

1. `PDFService` returns text from `data/mock_pdf_content.txt` instead of parsing a real PDF.
2. `MockMistralLLM` returns a canned markdown summary without calling Mistral's API.

The crew still runs through CrewAI end-to-end, so you can see how agents, tasks, tools, and the LLM slot together.

## Run with a real Mistral API key

```bash
export USE_MOCKS=false
export MISTRAL_API_KEY=your_key_here
python main.py --pdf path/to/real/document.pdf
```

When mocks are disabled:

- PDF text is extracted with `pypdf`
- CrewAI routes requests to Mistral via `LLM(model="mistral/mistral-small-latest")`

## Tests

```bash
pytest
```

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `USE_MOCKS` | `true` | Use mocked PDF content and LLM responses |
| `PDF_PATH` | `data/documents/sample_report.pdf` | Default PDF path for the crew |
| `MISTRAL_API_KEY` | — | Required when `USE_MOCKS=false` |
| `MISTRAL_MODEL` | `mistral/mistral-small-latest` | Mistral model identifier |

## Next steps

Typical extensions for a production RAG pipeline:

- Chunk documents and store embeddings in a vector database
- Add a retrieval tool backed by Chroma, Pinecone, or similar
- Split summarization into multi-agent steps (extract → retrieve → summarize)
- Add evaluation tests for summary quality
