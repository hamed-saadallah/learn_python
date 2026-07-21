"""Service layer for PDF extraction and LLM selection."""

from services.llm_factory import get_llm, use_mocks
from services.pdf_service import PDFService

__all__ = ["PDFService", "get_llm", "use_mocks"]
