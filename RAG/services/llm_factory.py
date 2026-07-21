from __future__ import annotations

import os

from crewai import LLM

from llm.mock_mistral_llm import MockMistralLLM


def use_mocks() -> bool:
    return os.getenv("USE_MOCKS", "true").lower() == "true"


def get_llm():
    """Return a Mistral-backed LLM, or a mock implementation for local dev."""
    model = os.getenv("MISTRAL_MODEL", "mistral/mistral-small-latest")

    if use_mocks():
        return MockMistralLLM(model=model.removeprefix("mistral/"))

    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        raise ValueError(
            "MISTRAL_API_KEY is required when USE_MOCKS=false. "
            "Copy .env.example to .env and add your key."
        )

    return LLM(model=model, api_key=api_key, temperature=0.2)
