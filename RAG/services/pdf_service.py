from __future__ import annotations

import os
from pathlib import Path

from pypdf import PdfReader


class PDFService:
    """Loads text from PDF files, with a mock path for local development."""

    def __init__(self, mock_content_path: Path | None = None) -> None:
        project_root = Path(__file__).resolve().parent.parent
        self._mock_content_path = mock_content_path or (
            project_root / "data" / "mock_pdf_content.txt"
        )

    def use_mocks(self) -> bool:
        return os.getenv("USE_MOCKS", "true").lower() == "true"

    def extract_text(self, pdf_path: str) -> str:
        """Return document text from a PDF file or mocked content."""
        if self.use_mocks():
            return self._load_mock_content(pdf_path)

        path = Path(pdf_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        reader = PdfReader(str(path))
        pages = [page.extract_text() or "" for page in reader.pages]
        text = "\n".join(pages).strip()
        if not text:
            raise ValueError(f"No extractable text found in PDF: {pdf_path}")
        return text

    def _load_mock_content(self, pdf_path: str) -> str:
        content = self._mock_content_path.read_text(encoding="utf-8").strip()
        header = (
            f"[MOCK PDF EXTRACTION]\n"
            f"Requested file: {pdf_path}\n"
            f"Source: {self._mock_content_path.name}\n"
            f"{'-' * 48}\n"
        )
        return f"{header}{content}"
