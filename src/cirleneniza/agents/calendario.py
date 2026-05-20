from crewai import Agent
from loguru import logger
from cirleneniza.tools.gemini import GeminiClient


import signal
from contextlib import contextmanager
from loguru import logger


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

    def __init__(self, gemini: "GeminiClient | None" = None):
        self.gemini = gemini if gemini is not None else GeminiClient()
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
        """Pesquisa científica sobre o tema — output limpo, sem formatação."""
        prompt = f"""Pesquise sobre: {topic}

Forneca em formato de lista numerada (sem Headers, sem marcadores de cena, sem timestamps):
1. ate 5 pontos cientificos-chave sobre o tema
2. Dados numericos relevantes se houver
3. Uma frase de contexto geral

Seja direto, factual, baseado em ciencia.
Idioma: portugues brasileiro."""
        result = self.gemini.generate(prompt, temperature=0.5)
        return {"topic": topic, "research": result.strip()}

    def generate_style_guide(self, topic: str, research: str) -> dict:
        """Gera Visual Style Guide conciso — apenas paletas e referencias."""
        prompt = f"""Com base no tema "{topic}" e pesquisa:

{research}

Forneca APENAS:
1. Paleta de cores: 3-4 cores com hex (ex: azul #2A5285, verde #38A169)
2. Tom visual: 1 frase (ex: "energetico e cientifico")
3. Referencia visual: 1 frase (ex: "pessoas treinando, alimentos naturais")
4. Composicao: 1 frase (ex: "close-up de maos e expressoes, fundos limpos")

MAXIMO 200 palavras total. Sem Headers, sem listas extensas, sem descricoes longas."""
        result = self.gemini.generate(prompt, temperature=0.6)
        return {"style_guide": result.strip()}

    def execute(self, topic: str) -> dict:
        """Executa pesquisa + Style Guide."""
        logger.info(f"Calendário: pesquisando {topic}")
        research = self.research_topic(topic)
        style_guide = self.generate_style_guide(topic, research["research"])
        return {
            "topic": topic,
            "research": research["research"],
            "style_guide": style_guide["style_guide"],
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