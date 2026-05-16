from crewai import Crew, Process
from cirleneniza.agents.calendario import get_agent as get_calendario
from cirleneniza.agents.revisor import get_agent as get_revisor
from cirleneniza.agents.diretor import get_agent as get_diretor
from cirleneniza.agents.roteirista import get_agent as get_roteirista
from cirleneniza.agents.diretor_arte import get_agent as get_diretor_arte
from cirleneniza.agents.narrador import Narrador
from cirleneniza.agents.editor_video import EditorVideo
from cirleneniza.agents.editor_audio import EditorAudio
from loguru import logger


class VideoCrew:
    """CrewAI crew for Canal Cirlene Niza pipeline."""

    def __init__(self):
        self.calendario = get_calendario()
        self.roteirista = get_roteirista()
        self.revisor = get_revisor()
        self.diretor = get_diretor()
        self.diretor_arte = get_diretor_arte()
        self.narrador = Narrador()
        self.editor_video = EditorVideo()
        self.editor_audio = EditorAudio()
        self.crew = None

    def build(self) -> Crew:
        """Build the crew with all Phase 1 + Phase 2 agents."""
        self.crew = Crew(
            agents=[
                self.calendario,
                self.roteirista,
                self.revisor,
                self.diretor,
                self.diretor_arte,
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