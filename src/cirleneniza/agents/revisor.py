import json
import re

from crewai import Agent
from loguru import logger
from cirleneniza.tools.minimax import MiniMaxClient


class RevisorEspecialista:
    """Agente Revisor Especialista — valida precisão científica dos roteiros."""

    def __init__(self, llm: MiniMaxClient | None = None):
        self.llm = llm or MiniMaxClient()
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
        """Revisa o roteiro e retorna JSON estruturado com claims."""
        prompt = f"""Revise este roteiro de vídeo de saúde:

{script}

Retorne SOMENTE JSON válido:
{{
  "claims": [
    {{
      "claim": "texto da afirmação exata do roteiro",
      "status": "ok | exagero | errado | vago",
      "suggestion": "correção sugerida ou null"
    }}
  ],
  "overall_score": 0.0
}}

Regras de classificação:
- "errado": dado falso ou contrafactual confirmado
- "exagero": verdadeiro mas sem nuance necessária
- "vago": afirmação sem dado concreto quando existe evidência numérica
- "ok": claim preciso, bem fundamentado
- overall_score: proporção de claims "ok" (0.0 a 1.0)
- Analise TODAS as afirmações de saúde/nutrição do roteiro"""
        raw = self.llm.generate(prompt, temperature=0.1)
        clean = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`")
        data = json.loads(clean)
        return data

    def execute(self, script: str) -> dict:
        """Executa revisão completa."""
        logger.info("Revisor: validando roteiro")
        data = self.validate_script(script)
        claims = data.get("claims", [])
        has_error = any(c.get("status") == "errado" for c in claims)
        return {
            "original_script": script,
            "claims": claims,
            "overall_score": data.get("overall_score", 1.0),
            "validation": json.dumps(data, ensure_ascii=False),  # compat string
            "status": "needs_revision" if has_error else "approved",
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