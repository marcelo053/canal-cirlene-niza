from crewai import Agent
from loguru import logger
from cirleneniza.tools.gemini import GeminiClient


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
        """Pesquisa científica sobre o tema."""
        prompt = f"""Pesquise sobre: {topic}

Forneça:
1. 3-5 pontos-chave científicos sobre o tema
2. Fontes reais (estudos, artigos) — pode usar fontes genéricas se não souber específicas
3. Dados numéricos relevantes (quantidades, percentages, prazos)

Idioma: português brasileiro."""
        result = self.gemini.generate(prompt, temperature=0.5)
        return {"topic": topic, "research": result}

    def generate_style_guide(self, topic: str, research: str) -> dict:
        """Gera Visual Style Guide para o tema."""
        prompt = f"""Com base na pesquisa sobre "{topic}":

{research}

Gere um Visual Style Guide com:
1. Paleta de cores sugerida (hex codes)
2. Tom visual (explicação de 1-2 frases)
3. Referências visuais (ex: "fotos de alimentos naturais", "pessoas em movimento")
4. Composição recomendada (close-up, wide, etc.)

Idioma: português brasileiro."""
        result = self.gemini.generate(prompt, temperature=0.6)
        return {"style_guide": result}

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