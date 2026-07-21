from __future__ import annotations

from typing import Any

from crewai.llms.base_llm import BaseLLM

MOCK_SUMMARY = """# Executive Summary

The document is a Q2 2026 quarterly product strategy report focused on
onboarding improvements, conversion growth, and enterprise readiness.

## Key Points

- Trial-to-paid conversion rose from 12% to 17%.
- Onboarding completion time fell from 42 to 28 minutes.
- Billing-related support tickets dropped 23% after a pricing refresh.
- Q3 priorities include AI-assisted search, CRM integrations, and upload performance.

## Conclusion

The team should continue the onboarding-first strategy while investing in
enterprise search and integration capabilities during Q3.
"""


class MockMistralLLM(BaseLLM):
    """Stand-in for Mistral AI used in local development and tests."""

    provider: str = "mistral"

    def call(
        self,
        messages: str | list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        callbacks: list[Any] | None = None,
        available_functions: dict[str, Any] | None = None,
        from_task: Any | None = None,
        from_agent: Any | None = None,
        response_model: Any | None = None,
    ) -> str:
        if available_functions and "read_pdf" in available_functions:
            pdf_path = _extract_pdf_path(messages)
            extracted_text = available_functions["read_pdf"](pdf_path=pdf_path)
            return (
                "[MOCK MISTRAL LLM]\n"
                "Simulated tool use: read_pdf\n\n"
                f"Extracted preview:\n{extracted_text[:280]}...\n\n"
                f"{MOCK_SUMMARY}"
            )

        return f"[MOCK MISTRAL LLM]\n\n{MOCK_SUMMARY}"


def _extract_pdf_path(messages: str | list[dict[str, Any]]) -> str:
    if isinstance(messages, str):
        return "data/documents/sample_report.pdf"

    for message in reversed(messages):
        content = message.get("content", "")
        if "data/" in content and ".pdf" in content:
            start = content.find("data/")
            end = content.find(".pdf", start) + 4
            return content[start:end]
    return "data/documents/sample_report.pdf"
