from crewai import Crew, Process
from cirleneniza.agents.calendario import get_agent as get_calendario
from cirleneniza.agents.revisor import get_agent as get_revisor
from cirleneniza.agents.diretor import get_agent as get_diretor
from cirleneniza.agents.roteirista import get_agent as get_roteirista
from loguru import logger


class VideoCrew:
    """CrewAI crew for Canal Cirlene Niza pipeline."""

    def __init__(self):
        self.calendario = get_calendario()
        self.roteirista = get_roteirista()
        self.revisor = get_revisor()
        self.diretor = get_diretor()
        self.crew = None

    def build(self) -> Crew:
        """Build the crew with all agents and tasks."""
        self.crew = Crew(
            agents=[
                self.calendario,
                self.roteirista,
                self.revisor,
                self.diretor,
            ],
            process=Process.sequential,
            verbose=True,
        )
        return self.crew

    def run(self, topic: str) -> dict:
        """Execute the crew pipeline."""
        if not self.crew:
            self.build()

        logger.info(f"VideoCrew: executando pipeline para '{topic}'")

        result = self.crew.kickoff(inputs={"topic": topic})

        return {
            "topic": topic,
            "result": result,
            "status": "completed",
        }


def get_crew() -> Crew:
    """Factory for VideoCrew."""
    return VideoCrew().build()