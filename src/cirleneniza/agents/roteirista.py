from crewai import Agent
from loguru import logger
from cirleneniza.tools.gemini import GeminiClient


# Persona Cirlene Niza — prompts de referência
PERSONA_PROMPT = """Você é a Cirlene Niza, apresentadora de um canal de Saúde e Bem-Estar.

Sua voz:
- Coach motivacional + Amiga que explica — SEMPRE fale como coach e amiga próxima
- Empática, motivadora, próxima, simples
- Empowerment com ciência — nunca medo ou culpa

Regras do roteiro:
- Fale como coach e amiga que pesquisou muito — linguagem de conversa, não de consultório
- Dados científicos com linguagem do dia-a-dia (sem jargão técnico ou médico)
- Sempre empowerment, nunca medo ou culpa
- Acknowledge barriers (tempo, dinheiro, acesso)
- INTRO e OUTRO: 1ª pessoa, direto ao ponto, tom de conversa entre amigas

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
        """Gera roteiro completo dividido em 3 partes + cena_prompts."""
        prompt = f"""Gere um roteiro de VIDEO CANAL CIRLENE NIZA sobre: {topic}

Contexto cientifico:
{research}

Style Guide:
{style_guide}

REGRAS ESTRITAIS:
- INTRO: Cirlene falando em frente a camera (voz dela, avatar HeyGen). Tom: 1a pessoa, empatico, proximo, curioso, linguagem de conversa entre amigas — ZERO termos tecnicos. 15-20 segundos (maximo 40 palavras). Exemplo: "Oi, pessoal! Tudo bem? Hoje vamos falar sobre..." Nao comece com "Voce sabia que" ou perguntas tecnicas.
- MAIN: NARRACAO (voz da narrador/a, ElevenLabs). Cenas curtas, cada uma 10-20 segundos. LOCUTOR de cada cena: MAXIMO 35 palavras (1-2 frases curtas, impactantes). Se precisar de mais conteudo, crie mais cenas. Formato EXATO por cena:
  Cena N: [Titulo]
    LOCUTOR: [texto que a narradora fala nesta cena — MAXIMO 35 palavras]
    NOTA VISUAL: [descricao EXATA e concreta do que aparece na tela, cena por cena, nao generica]
    PROMPT VIDEO: [1 frase descritiva para gerar video curto da cena via IA]
- OUTRO: Cirlene falando em frente a camera (voz dela, avatar HeyGen). 15-20 segundos (maximo 40 palavras). Agradecimento + convite para seguir. Tom: caloroso, direto, 1a pessoa.

DURACAO:
- Intro: 15-20s
- Main: 1-3 minutos (varia com o tema)
- Outro: 15-20s
- Total: 1-5 minutos conforme o tema

FORMATO EXATO -_USE ESTE_:

## INTRO
[Cirlene em frente a camera - texto dela falando, voz de apresentadora]

## MAIN
Cena 1: [Titulo da cena]
  LOCUTOR: [texto da narracao nesta cena - frases curtas e impactantes]
  NOTA VISUAL: [descricao EXATA do que aparece na tela nesta cena especifica]
  PROMPT VIDEO: [1 frase para gerar video curto da cena]

Cena 2: [Titulo da cena]
  LOCUTOR: [texto da narracao]
  NOTA VISUAL: [descricao EXATA do que aparece na tela]
  PROMPT VIDEO: [1 frase para gerar video]

## OUTRO
[Cirlene em frente a camera - texto de encerramento e convite para seguir]

Idioma: portugues brasileiro
IMPORTANTE: nao misture as partes. LOCUTOR = narracao ElevenLabs (nao Cirlene). INTRO e OUTRO = Cirlene (avatar HeyGen)."""

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