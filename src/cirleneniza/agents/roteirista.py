from crewai import Agent
from loguru import logger
from cirleneniza.tools.gemini import GeminiClient


# Persona Cirlene Niza — prompts de referência
PERSONA_PROMPT = """Você é a Cirlene Niza — coach motivacional e amiga próxima que pesquisou muito.

Sua voz: coach + amiga. Empática, motivadora, próxima, simples.
Empoderamento com ciência — NUNCA medo ou culpa.
Reconhece barreiras: tempo, dinheiro, acesso.
Tom: calorosa, acessível, sem ser bobinha. Animada mas não hiperativa.

Regras do roteiro:
- Fale como coach e amiga — linguagem de conversa, não de consultório
- INTRO/OUTRO: Cirlene falando em 1ª pessoa, avatar HeyGen (voz dela)
- MAIN: LOCUTOR ElevenLabs, frases curtas (10-20s por cena, MAX 35 palavras)
- Dados científicos com linguagem do dia-a-dia
- NUNCA termos técnicos, jargão médico ou tom de tabloide

Formato por cena no MAIN:
- LOCUTOR: MAX 35 palavras (1-2 frases curtas e impactantes)
- NOTA VISUAL: descrição EXATA do que aparece na tela
- PROMPT VIDEO: 1 frase para gerar vídeo curto via IA"""


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
        """Gera roteiro completo dividido em 3 partes + cena_prompts."""
        prompt = f"""Gere um roteiro de VIDEO CANAL CIRLENE NIZA sobre: {topic}

Contexto científico:
{research}

Style Guide:
{style_guide}

REGRAS ESTRITAIS:

**INTRO** — Cirlene em frente a câmera (voz dela, avatar HeyGen).
Tom: 1ª pessoa, empático, próximo, linguagem de conversa entre amigas.
MAX 40 palavras (15-20s). Exemplo: "Oi, pessoal! Tudo bem? Hoje vamos falar sobre..."
NÃO comece com "Você sabia que" ou perguntas técnicas.

**MAIN** — LOCUTOR ElevenLabs (narração). Cada cena: 10-20s, MAX 35 palavras.
LOCUTOR = frases curtas e impactantes. Se precisar de mais conteúdo, crie mais cenas.
Formato EXATO por cena:
  Cena N: [Título]
    LOCUTOR: [MAX 35 palavras - 1-2 frases curtas, impacto direto]
    NOTA VISUAL: [descrição EXATA do que aparece na tela nesta cena específica]
    PROMPT VIDEO: [1 frase descritiva para gerar vídeo curto via IA]

**OUTRO** — Cirlene em frente a câmera (voz dela). MAX 40 palavras.
Agradecimento + convite para seguir. Tom: caloroso, direto, 1ª pessoa.

DURAÇÃO TOTAL: 1-5 minutos conforme o tema
- Intro: 15-20s
- Main: 1-3 minutos (cenas curtas)
- Outro: 15-20s

FORMATO EXATO:

## INTRO
[Cirlene em frente a câmera - texto dela falando]

## MAIN
Cena 1: [Título]
  LOCUTOR: [texto da narração nesta cena - MAX 35 palavras]
  NOTA VISUAL: [descrição EXATA do que aparece na tela]
  PROMPT VIDEO: [1 frase para gerar vídeo curto]

Cena 2: [Título]
  LOCUTOR: [texto da narração]
  NOTA VISUAL: [descrição EXATA do que aparece na tela]
  PROMPT VIDEO: [1 frase para gerar vídeo]

## OUTRO
[Cirlene em frente a câmera - texto de encerramento e convite]

Idioma: português brasileiro
IMPORTANTE: LOCUTOR = narração ElevenLabs (não Cirlene). INTRO e OUTRO = Cirlene (avatar HeyGen).
LOCUTOR MAX 35 PALAVRAS POR CENA — frases curtas, não parágrafos."""

        result = self.gemini.generate(
            prompt,
            system=PERSONA_PROMPT,
            temperature=0.8,
        )
        return self._parse_script(result)

    def _parse_script(self, raw: str) -> dict:
        """Parse raw script into intro/main/outro sections."""
        intro, main, outro = "", "", ""
        lines = raw.split("\n")
        current = None
        buffer = []

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("## INTRO"):
                current = "intro"
                continue
            elif stripped.startswith("## MAIN"):
                if buffer and current == "intro":
                    intro = "\n".join(buffer).strip()
                    buffer = []
                current = "main"
                continue
            elif stripped.startswith("## OUTRO"):
                if buffer and current == "main":
                    main = "\n".join(buffer).strip()
                    buffer = []
                current = "outro"
                continue
            if current:
                buffer.append(line)

        if buffer:
            if current == "intro":
                intro = "\n".join(buffer).strip()
            elif current == "main":
                main = "\n".join(buffer).strip()
            elif current == "outro":
                outro = "\n".join(buffer).strip()

        cena_prompts = self._extract_cena_prompts(main)

        return {
            "intro": intro,
            "main": main,
            "outro": outro,
            "cena_prompts": cena_prompts,
            "full_script": f"## INTRO\n{intro}\n\n## MAIN\n{main}\n\n## OUTRO\n{outro}",
        }

    def _extract_cena_prompts(self, main_section: str) -> list[dict]:
        """Extract scene data (prompts, visuals, narration) from MAIN section."""
        prompts = []
        lines = main_section.split("\n")
        current_scene = None
        locutor_buf = []
        nota_buf = []
        prompt_buf = []
        field = None

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("Cena ") or stripped.startswith("Cena-"):
                if current_scene:
                    prompts.append({
                        "scene": current_scene,
                        "locutor": " ".join(locutor_buf).strip(),
                        "nota_visual": " ".join(nota_buf).strip(),
                        "prompt": " ".join(prompt_buf).strip(),
                    })
                current_scene = stripped
                locutor_buf, nota_buf, prompt_buf = [], [], []
                field = None
            elif stripped.startswith("LOCUTOR:"):
                field = "locutor"
                locutor_buf.append(stripped.replace("LOCUTOR:", "").strip())
            elif stripped.startswith("NOTA VISUAL:") or stripped.startswith("NOTA:"):
                field = "nota"
                nota_buf.append(stripped.replace("NOTA VISUAL:", "").replace("NOTA:", "").strip())
            elif stripped.startswith("PROMPT VIDEO:") or stripped.startswith("PROMPT:"):
                field = "prompt"
                prompt_buf.append(stripped.replace("PROMPT VIDEO:", "").replace("PROMPT:", "").strip())
            elif field and stripped:
                if field == "locutor":
                    locutor_buf.append(stripped)
                elif field == "nota":
                    nota_buf.append(stripped)
                elif field == "prompt":
                    prompt_buf.append(stripped)

        if current_scene:
            prompts.append({
                "scene": current_scene,
                "locutor": " ".join(locutor_buf).strip(),
                "nota_visual": " ".join(nota_buf).strip(),
                "prompt": " ".join(prompt_buf).strip(),
            })

        return prompts

    def apply_correction(
        self,
        current: dict,
        correction: str,
        step: str,
    ) -> dict:
        """Apply user correction to a specific script part."""
        if step == "intro":
            prompt = f"""Ajusta o INTRO do roteiro conforme solicitado:

CORREÇÃO SOLICITADA: {correction}

INTRO ATUAL:
{current.get('intro', '')}

Reescreve APENAS o INTRO. Mantém o mesmo formato: ## INTRO + texto."""
        elif step == "main":
            prompt = f"""Ajusta o MAIN (cenas) do roteiro conforme solicitado:

CORREÇÃO SOLICITADA: {correction}

MAIN ATUAL:
{current.get('main', '')}

Reescreve APENAS o MAIN. Mantém o mesmo formato de cenas."""
        elif step == "outro":
            prompt = f"""Ajusta o OUTRO do roteiro conforme solicitado:

CORREÇÃO SOLICITADA: {correction}

OUTRO ATUAL:
{current.get('outro', '')}

Reescreve APENAS o OUTRO. Mantém o mesmo formato: ## OUTRO + texto."""
        else:
            prompt = f"""Ajusta o roteiro completo conforme solicitado:

CORREÇÃO SOLICITADA: {correction}

ROTEIRO ATUAL:
Intro: {current.get('intro', '')}
Main: {current.get('main', '')}
Outro: {current.get('outro', '')}

Retorna o roteiro completo com 3 partes."""

        result = self.gemini.generate(prompt, system=PERSONA_PROMPT, temperature=0.8)
        return self._parse_script(result)

    def generate_thumbnail_prompts(self, topic: str, style_guide: str) -> list[str]:
        """Gera prompts de thumbnail para o Diretor de Arte — formato Flux-compatível em inglês."""
        prompt = f"""Generate 2 image generation prompts for a YouTube thumbnail about: {topic}

RULES (mandatory):
- Write in ENGLISH only
- Describe ONLY visual elements — no text, no titles, no words in the image
- Be concrete and specific: describe food, ingredients, colors, lighting, composition
- Style: photorealistic, warm lighting, professional food photography or lifestyle photo
- Color palette: warm terracotta tones, orange accents (#E07B39), clean background
- NO cartoon faces, NO people faces, NO abstract shapes, NO random objects
- FORMAT: return exactly 2 prompts, each on its own line, no numbering, no labels, no blank lines

Example for "banana pancake recipe":
Fluffy golden banana pancakes stacked on a rustic wooden plate, fresh banana slices on top, warm honey dripping, soft morning light, food photography style, warm terracotta background, appetizing and inviting
Close-up of ripe bananas and oat flour on a kitchen counter, warm orange tones, natural daylight, clean minimal composition, healthy fitness lifestyle aesthetic

Now generate 2 prompts for: {topic}"""
        result = self.gemini.generate(prompt, temperature=0.6)
        # pega linhas não-vazias que parecem prompts reais (>30 chars)
        prompts = [
            line.strip()
            for line in result.strip().split("\n")
            if line.strip() and len(line.strip()) > 30
            and not line.strip().startswith(("#", "-", "*", "1.", "2.", "Prompt"))
        ]
        return prompts[:2]

    def execute(self, topic: str, research: str, style_guide: str) -> dict:
        """Executa geração de roteiro + thumbnail prompts."""
        logger.info(f"Roteirista: gerando roteiro para {topic}")
        script_data = self.generate_script(topic, research, style_guide)
        thumbnail_prompts = self.generate_thumbnail_prompts(topic, style_guide)
        return {
            "topic": topic,
            "intro": script_data["intro"],
            "main": script_data["main"],
            "outro": script_data["outro"],
            "full_script": script_data["full_script"],
            "cena_prompts": script_data["cena_prompts"],
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