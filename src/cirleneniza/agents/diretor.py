from crewai import Agent
from loguru import logger


class Diretor:
    """Agente Diretor — orquestra o pipeline e delega para outros agentes."""

    def __init__(self):
        self.name = "Diretor"
        self.role = (
            "Diretor de conteúdo do Canal Cirlene Niza. "
            "Orquestra o pipeline de produção: pesquisa → roteiro → revisão → aprovação. "
            "Delega tarefas para os agentes especializados e valida o resultado final."
        )
        self.backstory = (
            "Produtor de conteúdo digital especializado em saúde e bem-estar. "
            "Coordena toda a produção do canal, garantindo qualidade e consistência. "
            "Conhece cada agente e sabe quando usar cada um."
        )
        self.goal = "Entregar roteiros aprovados e prontos para produção."

    def orchestrate(
        self,
        topic: str,
        calendario_output: dict,
        roteirista_output: dict,
        revisor_output: dict,
    ) -> dict:
        """Orquestra o fluxo completo."""
        logger.info(f"Diretor: orquestrando produção para '{topic}'")
        return {
            "topic": topic,
            "research": calendario_output.get("research"),
            "style_guide": calendario_output.get("style_guide"),
            "script": roteirista_output.get("script"),
            "thumbnail_prompts": roteirista_output.get("thumbnail_prompts"),
            "validation": revisor_output.get("validation"),
            "status": "approved" if revisor_output.get("status") == "approved" else "needs_revision",
        }


def get_agent() -> Agent:
    """Factory para crewAI agent — manager role."""
    diretor = Diretor()
    return Agent(
        name=diretor.name,
        role=diretor.role,
        backstory=diretor.backstory,
        goal=diretor.goal,
        tools=[],
        verbose=True,
        allow_delegation=True,
    )