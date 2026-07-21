from __future__ import annotations

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, llm, task

from rag_crew.tools.pdf_reader import PDFReaderTool
from services.llm_factory import get_llm


@CrewBase
class RagCrew:
    """CrewAI crew that reads a PDF and produces a summary."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @llm
    def mistral(self):
        return get_llm()

    @agent
    def pdf_summarizer(self) -> Agent:
        return Agent(
            config=self.agents_config["pdf_summarizer"],  # type: ignore[index]
            llm=self.mistral(),
            tools=[PDFReaderTool()],
            verbose=True,
        )

    @task
    def summarize_pdf(self) -> Task:
        return Task(
            config=self.tasks_config["summarize_pdf"],  # type: ignore[index]
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
