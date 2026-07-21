import os

import pytest

from llm.mock_mistral_llm import MOCK_SUMMARY, MockMistralLLM
from rag_crew.crew import RagCrew
from rag_crew.tools.pdf_reader import PDFReaderTool
from services.llm_factory import get_llm, use_mocks
from services.pdf_service import PDFService


@pytest.fixture(autouse=True)
def enable_mocks(monkeypatch):
    monkeypatch.setenv("USE_MOCKS", "true")


def test_pdf_service_returns_mock_content():
    service = PDFService()
    text = service.extract_text("data/documents/sample_report.pdf")

    assert "[MOCK PDF EXTRACTION]" in text
    assert "Quarterly Product Strategy Report" in text


def test_pdf_reader_tool_uses_mock_content():
    tool = PDFReaderTool()
    text = tool._run("data/documents/sample_report.pdf")

    assert "Q2 2026" in text


def test_mock_mistral_llm_returns_summary():
    llm = MockMistralLLM(model="mistral-small-latest")
    response = llm.call("Summarize the quarterly report.")

    assert "[MOCK MISTRAL LLM]" in response
    assert "Executive Summary" in response
    assert MOCK_SUMMARY.splitlines()[2] in response


def test_get_llm_uses_mock_by_default():
    assert use_mocks() is True
    assert isinstance(get_llm(), MockMistralLLM)


def test_get_llm_requires_api_key_when_mocks_disabled(monkeypatch):
    monkeypatch.setenv("USE_MOCKS", "false")
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)

    with pytest.raises(ValueError, match="MISTRAL_API_KEY"):
        get_llm()


def test_rag_crew_can_be_built():
    crew = RagCrew().crew()

    assert len(crew.agents) == 1
    assert len(crew.tasks) == 1
    assert crew.tasks[0].output_file == "output/summary.md"
