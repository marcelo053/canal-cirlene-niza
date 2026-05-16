from crewai import Agent
from loguru import logger
from cirleneniza.tools.gemini import GeminiClient


# Persona Cirlene Niza — prompts de referência
PERSONA_PROMPT = """Você é a Cirlene Niza, apresentadora de um canal de Saúde e Bem-Estar.

Sua voz:
- Coach motivacional + Amiga que explica
- Empática, motivadora, próxima, simples
- Empowerment com ciência — nunca medo ou culpa

Regras do roteiro:
- "Não fale como médica, fale como amiga que pesquisou muito"
- "Dados científicos com linguagem do dia-a-dia"
- "Sempre empowerment, nunca medo ou culpa"
- "Acknowledge barriers (tempo, dinheiro, acesso)"

Tom: calorosa, acessível, sem ser bobinha. Animada mas não hiperativa.
Formato: script com cenas numeradas, cada cena com:
- Título da cena
- Texto de narração
- Notas de direção (opcional)"""


class RoteiristaCirleneNiza:
    """Agente Roteirista — scripts no estilo Cirlene Niza."""

    def __init__(self):
        self.gemini = GeminiClient()
        self.name = "Roteirista"
        self.role = (
            "Escritor de roteiros para vídeos de saúde e bem-estar. "
            "Gera scripts com a voz da Cirlene Niza — empática, motivadora e acessível. "
            "Cada roteiro inclui cenas com narração e notas visuais."
        )
        self.backstory = PERSONA_PROMPT
        self.goal = "Gerar roteiro completo e engajante que empodera a audiência."

    def generate_script(
        self,
        topic: str,
        research: str,
        style_guide: str,
    ) -> dict:
        """Gera roteiro completo com cenas."""
        prompt = f"""Gere um roteiro de vídeo sobre: {topic}

Contexto científico:
{research}

Style Guide:
{style_guide}

Formato do roteiro:
1. Título do vídeo
2. Hook (abertura que prende atenção — 5-10 segundos)
3. Cenas numeradas (5-8 cenas):
   - Cena 1: [Título]
     Narração: [texto para narração]
     Notas visuais: [descrição do que aparece na tela]
4. CTA (call-to-action) no final

Duração estimada: 3-5 minutos
Idioma: português brasileiro"""

        result = self.gemini.generate(
            prompt,
            system=PERSONA_PROMPT,
            temperature=0.8,
        )
        return {"script": result}

    def generate_thumbnail_prompts(self, topic: str, style_guide: str) -> list[str]:
        """Gera prompts de thumbnail para o Diretor de Arte."""
        prompt = f"""Gere 2 prompts de thumbnail para um vídeo sobre: {topic}

Style Guide: {style_guide}

Cada prompt deve:
- Ser detalhado e descritivo
- Incluir referência à paleta de cores
- Descrever a composição (texto, imagem, layout)
- Ser em português para fal.ai

Output: lista de 2 prompts, um por thumbnail."""
        result = self.gemini.generate(prompt, temperature=0.7)
        prompts = [line.strip() for line in result.split("\n") if line.strip()]
        return prompts[:2]

    def execute(self, topic: str, research: str, style_guide: str) -> dict:
        """Executa geração de roteiro + thumbnail prompts."""
        logger.info(f"Roteirista: gerando roteiro para {topic}")
        script = self.generate_script(topic, research, style_guide)
        thumbnail_prompts = self.generate_thumbnail_prompts(topic, style_guide)
        return {
            "topic": topic,
            "script": script["script"],
            "thumbnail_prompts": thumbnail_prompts,
        }


def get_agent() -> Agent:
    """Factory para crewAI agent."""
    roteirista = RoteiristaCirleneNiza()
    return Agent(
        name=roteirista.name,
        role=roteirista.role,
        backstory=roteirista.backstory,
        goal=roteirista.goal,
        tools=[],
        verbose=True,
    )