from crewai import Agent
from loguru import logger
from cirleneniza.tools.minimax import MiniMaxClient


class RevisorEspecialista:
    """Agente Revisor Especialista — valida precisão científica dos roteiros."""

    def __init__(self, gemini: MiniMaxClient | None = None):
        self.gemini = gemini or MiniMaxClient()
        self.name = "Revisor Especialista"
        self.role = (
            "Revisor científico especialista em saúde e nutrição. "
            "Valida todos os claims do roteiro — remove exagero, corrige erros, "
            "adiciona fontes quando necessário."
        )
        self.backstory = (
            "Profissional de saúde com experiência em análise de literatura científica. "
            "Sabe identificar claims falsos, hiperbólicos ou não fundamentados. "
            "Comprometido com informação de qualidade."
        )
        self.goal = "Garantir que todo roteiro seja scientificamente preciso e motivador."

    def validate_script(self, script: str) -> dict:
        """Revisa o roteiro e retorna correções."""
        prompt = f"""Revise este roteiro de vídeo de saúde:

{script}

Para cada claim/afirmação no roteiro, classifique:
- OK: claim preciso e bem fundamentado
- EXAGERO: claim exagerado que precisa ser atenuado
- ERRADO: claim incorreto que precisa ser substituído
- VAGO: claim muito genérico que precisa de dado específico

Se encontrar problemas, sugira correção com fonte (genérica se necessário).
Se tudo estiver ok, confirme com "APROVADO"."""

        result = self.gemini.generate(prompt, temperature=0.3)
        return {"validation": result}

    def execute(self, script: str) -> dict:
        """Executa revisão completa."""
        logger.info("Revisor: validando roteiro")
        validation = self.validate_script(script)
        return {
            "original_script": script,
            "validation": validation["validation"],
            "status": "needs_revision" if "ERRADO" in validation["validation"] else "approved",
        }


def get_agent() -> Agent:
    """Factory para crewAI agent."""
    revisor = RevisorEspecialista()
    return Agent(
        name=revisor.name,
        role=revisor.role,
        backstory=revisor.backstory,
        goal=revisor.goal,
        tools=[],
        verbose=True,
    )