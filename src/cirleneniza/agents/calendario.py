import json
import re
import signal
from contextlib import contextmanager

from crewai import Agent
from loguru import logger
from cirleneniza.tools.minimax import MiniMaxClient


@contextmanager
def _timeout(seconds: int):
    def handler(signum, frame):
        raise TimeoutError(f"Timed out after {seconds}s")
    old = signal.signal(signal.SIGALRM, handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


class CalendarioEditorial:
    """Agente Calendário Editorial — pesquisa científica e Style Guide."""

    def __init__(self, llm: "MiniMaxClient | None" = None):
        self.llm = llm if llm is not None else MiniMaxClient()
        self.name = "Calendário Editorial"
        self.role = (
            "Pesquisador de saúde e bem-estar. "
            "Pesquisa bases científicas sobre o tema e gera um Visual Style Guide. "
            "Nunca inventa dados — sempre cita fontes verificáveis."
        )
        self.backstory = (
            "Especialista em pesquisa de saúde com formação em nutrição. "
            "Sabe encontrar os estudos mais relevantes e traduzir complexidade científica "
            "para informação acessível."
        )
        self.goal = "Fornecer contexto científico sólido e Visual Style Guide para o Roteirista."

    def research_topic(self, topic: str) -> dict:
        """Pesquisa científica sobre o tema — retorna dict estruturado + string para compat."""
        prompt = f"""Pesquise sobre: {topic}

Retorne SOMENTE JSON válido (sem markdown, sem explicações):
{{
  "points": ["ponto científico 1", "ponto científico 2", "até 5 pontos"],
  "key_data": ["dado numérico 1 com número concreto"]
}}

Seja direto, factual, baseado em ciência. Idioma: português brasileiro."""
        raw = self.llm.generate(prompt, temperature=0.5)
        clean = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`")
        data = json.loads(clean)
        research_text = "\n".join(data.get("points", []) + data.get("key_data", []))
        return {"topic": topic, "research": research_text, "research_data": data}

    def generate_style_guide(self, topic: str, research: str) -> dict:
        """Gera Visual Style Guide — retorna dict estruturado + string formatada para compat."""
        prompt = f"""Com base no tema "{topic}" e pesquisa:
{research}

Retorne SOMENTE JSON válido (sem markdown):
{{
  "palette": ["#E07B39", "#F5F0E8", "#2D5A27", "#FFFFFF"],
  "visual_tone": "descrição em 1 frase",
  "visual_reference": "referência visual em 1 frase",
  "composition": "instrução de composição em 1 frase"
}}"""
        raw = self.llm.generate(prompt, temperature=0.6)
        clean = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`")
        data = json.loads(clean)
        style_text = (
            f"Paleta: {', '.join(data['palette'])}\n"
            f"Tom visual: {data['visual_tone']}\n"
            f"Referencia visual: {data['visual_reference']}\n"
            f"Composicao: {data['composition']}"
        )
        return {"style_guide": style_text, "style_guide_data": data}

    def execute(self, topic: str) -> dict:
        """Executa pesquisa + Style Guide."""
        logger.info(f"Calendário: pesquisando {topic}")
        research = self.research_topic(topic)
        style_guide = self.generate_style_guide(topic, research["research"])
        return {
            "topic": topic,
            "research": research["research"],           # string — compat
            "research_data": research["research_data"],  # dict — novo
            "style_guide": style_guide["style_guide"],           # string — compat
            "style_guide_data": style_guide["style_guide_data"],  # dict — novo
        }


def get_agent() -> Agent:
    """Factory para crewAI agent."""
    calendario = CalendarioEditorial()
    return Agent(
        name=calendario.name,
        role=calendario.role,
        backstory=calendario.backstory,
        goal=calendario.goal,
        tools=[],
        verbose=True,
    )