"""Agente Gerador de Slides Científicos — extrai dados de pesquisa e renderiza slides Remotion."""
import json
import re
from loguru import logger

from cirleneniza.tools.minimax import MiniMaxClient
from cirleneniza.tools.minio import MinIOClient
from cirleneniza.tools.remotion import RemotionRenderer

_EXTRACT_PROMPT = """Você analisa texto de pesquisa científica e extrai dados estruturados para slides de apresentação.

TEXTO DE PESQUISA:
{research}

TÓPICO DO VÍDEO: {topic}

Extraia 2 a 4 slides científicos do texto. Cada slide deve usar UM dos layouts abaixo:

## LAYOUTS DISPONÍVEIS

**StatCard** — um número/percentual impactante
{{
  "composition": "StatCard",
  "props": {{
    "stat": "73%",
    "description": "descrição clara e direta em português",
    "source": "Fonte científica, Ano",
    "topic": "{topic}"
  }}
}}

**CircleStat** — percentual em arco circular (use quando o número for o foco principal)
{{
  "composition": "CircleStat",
  "props": {{
    "value": 73,
    "unit": "%",
    "description": "descrição clara em português",
    "source": "Fonte científica, Ano",
    "topic": "{topic}"
  }}
}}

**ComparisonBar** — comparativo antes/depois com valores numéricos
{{
  "composition": "ComparisonBar",
  "props": {{
    "title": "Título do comparativo",
    "before": {{"label": "Antes", "value": 82}},
    "after": {{"label": "Depois (X semanas)", "value": 31}},
    "unit": "%",
    "source": "Fonte científica, Ano"
  }}
}}

**StudyQuote** — citação direta de estudo com palavra-chave em destaque
{{
  "composition": "StudyQuote",
  "props": {{
    "quote": "Citação do estudo em português",
    "highlight": "parte mais impactante da citação",
    "study": "Nome do periódico científico",
    "year": 2023,
    "topic": "{topic}"
  }}
}}

**BenefitsList** — lista de 3 a 5 benefícios ou sintomas com emoji
{{
  "composition": "BenefitsList",
  "props": {{
    "title": "Título da lista",
    "items": [
      {{"icon": "✅", "text": "Benefício ou sintoma em português"}},
      {{"icon": "✅", "text": "Benefício ou sintoma em português"}}
    ],
    "source": "Fonte científica, Ano",
    "topic": "{topic}"
  }}
}}

**TimelineProgress** — progresso ao longo do tempo (2 a 4 milestones)
{{
  "composition": "TimelineProgress",
  "props": {{
    "title": "Título da linha do tempo",
    "milestones": [
      {{"label": "Semana 1", "value": "-30%", "description": "Descrição curta"}},
      {{"label": "Semana 4", "value": "-58%", "description": "Descrição curta"}}
    ],
    "source": "Fonte científica, Ano",
    "topic": "{topic}"
  }}
}}

**ScientificDefinition** — definição de termo científico em linguagem simples
{{
  "composition": "ScientificDefinition",
  "props": {{
    "term": "Termo Científico",
    "pronunciation": "/pronúncia/",
    "definition": "Definição técnica em português",
    "analogy": "Explicação em linguagem cotidiana, como se explicasse para uma amiga",
    "topic": "{topic}"
  }}
}}

## REGRAS
- Use APENAS dados presentes no texto de pesquisa — não invente números
- Se o texto não tiver dados suficientes para um tipo, pule esse tipo
- Prefira slides com dados concretos (números, percentuais, prazos)
- Máximo 4 slides — qualidade > quantidade
- Todos os textos em PORTUGUÊS BRASILEIRO
- Sources: use nomes reais de periódicos se mencionados, ou "Literatura Científica, [ano]" se não especificado

## FORMATO DE SAÍDA
Retorne APENAS um array JSON válido, sem markdown, sem explicações:
[
  {{slide 1}},
  {{slide 2}},
  ...
]"""


class GeradorSlidesCientificos:
    """Extrai dados científicos do texto de pesquisa e renderiza slides Remotion."""

    def __init__(
        self,
        minio: MinIOClient | None = None,
        renderer: RemotionRenderer | None = None,
    ):
        self.gemini = MiniMaxClient()
        self.renderer = renderer or RemotionRenderer(minio)
        self.name = "Gerador de Slides Científicos"

    # ------------------------------------------------------------------
    # Extract slide specs from research text
    # ------------------------------------------------------------------

    def extract_slides(self, research: str, topic: str) -> list[dict]:
        """Use LLM to extract structured slide data from research text."""
        prompt = _EXTRACT_PROMPT.format(research=research, topic=topic)
        raw = self.gemini.generate(prompt, temperature=0.3, max_tokens=4096)

        # Strip markdown code fences if present
        raw = re.sub(r"```(?:json)?\s*", "", raw).strip()

        try:
            slides = json.loads(raw)
            if not isinstance(slides, list):
                raise ValueError("Expected JSON array")
            logger.info(f"GeradorSlides: extracted {len(slides)} slide specs for '{topic}'")
            return slides
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"GeradorSlides: JSON parse failed: {e}\nRaw: {raw[:400]}")
            return []

    # ------------------------------------------------------------------
    # Main execute
    # ------------------------------------------------------------------

    def execute(
        self,
        research: str,
        topic: str,
        production_id: int | None = None,
    ) -> dict:
        """Extract slides from research and render all. Returns rendered slide URLs."""
        logger.info(f"GeradorSlides: iniciando para '{topic}'")

        slides = self.extract_slides(research, topic)
        if not slides:
            logger.warning("GeradorSlides: nenhum slide extraído")
            return {"slides": [], "status": "empty"}

        results = self.renderer.render_batch(slides, production_id=production_id)

        successful = [r for r in results if r.get("url")]
        failed = [r for r in results if not r.get("url")]

        if failed:
            logger.warning(
                f"GeradorSlides: {len(failed)}/{len(results)} slides falharam: "
                + ", ".join(f["composition"] for f in failed)
            )

        logger.info(f"GeradorSlides: {len(successful)} slides renderizados para '{topic}'")
        return {
            "slides": results,
            "slide_urls": [r["url"] for r in successful],
            "topic": topic,
            "status": "done" if successful else "failed",
        }
