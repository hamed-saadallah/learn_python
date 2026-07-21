#!/usr/bin/env python3
"""Entry point for the PDF summarization RAG crew."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from dotenv import load_dotenv

from rag_crew.crew import RagCrew
from services.llm_factory import use_mocks
from services.pdf_service import PDFService


def run(pdf_path: str | None = None) -> str:
    load_dotenv()

    resolved_pdf_path = pdf_path or os.getenv(
        "PDF_PATH", "data/documents/sample_report.pdf"
    )
    project_root = Path(__file__).resolve().parent

    print("RAG PDF Summarizer")
    print("=" * 40)
    print(f"PDF path: {resolved_pdf_path}")
    print(f"Mock mode: {use_mocks()}")
    print()

    if use_mocks():
        preview = PDFService().extract_text(resolved_pdf_path)
        print("Mock PDF extraction preview:")
        print(preview[:320] + ("..." if len(preview) > 320 else ""))
        print()

    inputs = {"pdf_path": str(project_root / resolved_pdf_path)}
    result = RagCrew().crew().kickoff(inputs=inputs)

    print("\nCrew finished.")
    print("-" * 40)
    print(result)
    return str(result)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Summarize a PDF using a CrewAI agent and Mistral AI."
    )
    parser.add_argument(
        "--pdf",
        dest="pdf_path",
        help="Path to the PDF file (defaults to PDF_PATH env var).",
    )
    args = parser.parse_args()
    run(pdf_path=args.pdf_path)


if __name__ == "__main__":
    main()
