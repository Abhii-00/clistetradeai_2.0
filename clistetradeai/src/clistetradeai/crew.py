from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent


@CrewBase
class Clistetradeai:
    """Financial intelligence reasoning crew."""

    agents: list[BaseAgent]
    tasks: list[Task]

    @agent
    def technical_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["technical_agent"],  # type: ignore[index]
            verbose=True,
        )

    @agent
    def sentiment_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["sentiment_agent"],  # type: ignore[index]
            verbose=True,
        )

    @agent
    def risk_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["risk_agent"],  # type: ignore[index]
            verbose=True,
        )

    @agent
    def decision_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["decision_agent"],  # type: ignore[index]
            verbose=True,
        )

    @task
    def technical_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config["technical_analysis_task"],  # type: ignore[index]
        )

    @task
    def sentiment_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config["sentiment_analysis_task"],  # type: ignore[index]
        )

    @task
    def risk_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config["risk_analysis_task"],  # type: ignore[index]
            context=[
                self.technical_analysis_task(),
                self.sentiment_analysis_task(),
            ],
        )

    @task
    def decision_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config["decision_analysis_task"],  # type: ignore[index]
            context=[
                self.technical_analysis_task(),
                self.sentiment_analysis_task(),
                self.risk_analysis_task(),
            ],
        )

    @crew
    def crew(self) -> Crew:
        """Creates the financial intelligence reasoning crew."""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
