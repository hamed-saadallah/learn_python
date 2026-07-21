from __future__ import annotations

from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from services.pdf_service import PDFService


class PDFReaderInput(BaseModel):
    pdf_path: str = Field(
        ...,
        description="Absolute or relative path to the PDF file to read.",
    )


class PDFReaderTool(BaseTool):
    name: str = "read_pdf"
    description: str = (
        "Extract plain text from a PDF document. "
        "Provide the file path as pdf_path."
    )
    args_schema: Type[BaseModel] = PDFReaderInput

    def _run(self, pdf_path: str) -> str:
        return PDFService().extract_text(pdf_path)
