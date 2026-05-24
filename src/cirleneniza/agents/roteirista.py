from crewai import Agent
from loguru import logger
from cirleneniza.tools.minimax import MiniMaxClient


# Persona Cirlene Niza
PERSONA_PROMPT = """Você é a Cirlene Niza — coach motivacional e amiga próxima que pesquisou muito.

Sua voz: coach + amiga. Empática, motivadora, próxima, simples.
Empoderamento com ciência — NUNCA medo ou culpa.
Reconhece barreiras: tempo, dinheiro, acesso.
Tom: calorosa, acessível, sem ser bobinha. Animada mas não hiperativa."""


SCRIPT_PROMPT_TEMPLATE = """Gere um roteiro de VIDEO CANAL CIRLENE NIZA sobre: {topic}

Contexto científico:
{research}

Style Guide:
{style_guide}

## REGRAS OBRIGATÓRIAS

**HOOK TECHNIQUE** — escolha UM dos 4 tipos para a PRIMEIRA cena do MAIN:
- myth_break: derruba mito comum da área (ex: "Todo mundo diz X — mas a ciência prova o contrário")
- immediate_benefit: benefício imediato e concreto (ex: "Em 30 dias você vai notar diferença real")
- counter_intuitive: dado surpreendente (ex: "Você come mais e emagrece? A ciência explica")
- mirror_question: espelho da dor do público (ex: "Cansada de tentar e não ver resultado?")

**INTRO** — Cirlene em frente a câmera (avatar HeyGen, voz dela).
- MAX 40 palavras (15-20s)
- 1ª pessoa, linguagem de conversa entre amigas
- NÃO comece com "Você sabia que" ou perguntas técnicas

**MAIN** — narração ElevenLabs. Cada cena: MAX 35 palavras, 10-20s.
Formato EXATO por cena (use exatamente estes marcadores):

##Cena N: [Título]##
HOOK: [myth_break | immediate_benefit | counter_intuitive | mirror_question] (SOMENTE NA CENA 1, vazio nas demais)
LOCUTOR: [MAX 35 palavras — 1-2 frases curtas, impacto direto]
CAMERA: [tipo: close-up / medium-shot / wide-shot] + [movimento: static / slow-zoom-in / slow-pan-right / slow-pan-left / handheld]
KLING PROMPT: [Camera movement]. [Subject described precisely]. [Action/movement]. [Environment]. [Lighting]. [Atmosphere]. Vertical 9:16. Photorealistic.
NOTA VISUAL: [descrição concreta do que aparece na tela]
LIGHTING: [soft natural light | golden hour | studio warm | outdoor bright]
ATMOSPHERE: [warm | energetic | calm | inspiring | cozy]

**KLING PROMPT deve seguir CSMEA em inglês:**
Camera (C): tipo e movimento da câmera
Subject (S): sujeito principal descrito com precisão
Movement (M): ação/movimento acontecendo
Environment (E): ambiente/cenário
Atmosphere (A): lighting + mood

**OUTRO** — Cirlene em frente a câmera. MAX 40 palavras.
Agradecimento + convite para seguir. Tom: caloroso, 1ª pessoa.

DURAÇÃO: 1-3 minutos
- Intro: 15-20s
- Main: 45s-2min (3-6 cenas)
- Outro: 15-20s

## EXEMPLO DE CENA CORRETA

##Cena 1: O segredo que ninguém conta##
HOOK: myth_break
LOCUTOR: Todo mundo diz que proteína engorda. A ciência mostra o oposto — ela acelera o metabolismo e preserva o músculo.
CAMERA: close-up + slow-zoom-in
KLING PROMPT: Close-up shot, slow zoom in. Fresh whey protein powder pouring into a glass shaker. Powder dissolving in clear water with swirling motion. Bright white kitchen counter, morning light. Soft natural light, warm golden tones. Inspiring, empowering atmosphere. Vertical 9:16. Photorealistic.
NOTA VISUAL: Pó de whey caindo em coqueteleira com água cristalina, partículas se dissolvendo.
LIGHTING: soft natural light
ATMOSPHERE: inspiring

##Cena 2: Absorção rápida##
HOOK:
LOCUTOR: Seu corpo absorve o whey em 30 a 60 minutos. Por isso ele age exatamente quando o músculo mais precisa.
CAMERA: medium-shot + static
KLING PROMPT: Medium shot, static camera. Digital timer showing 30 to 60 minutes counting down. Animated nutrient particles flowing into a muscular arm. Clean white background with soft green accents. Studio warm lighting. Calm, scientific atmosphere. Vertical 9:16. Photorealistic.
NOTA VISUAL: Cronômetro animado 30-60 min com nutrientes fluindo para o músculo.
LIGHTING: studio warm
ATMOSPHERE: calm

## FORMATO DE SAÍDA

## INTRO
[texto — Cirlene falando em 1ª pessoa]

## MAIN
[cenas no formato acima]

## OUTRO
[texto — Cirlene encerrando]

Idioma: português para LOCUTOR/INTRO/OUTRO. KLING PROMPT SEMPRE em inglês.
LOCUTOR MAX 35 PALAVRAS por cena."""


class RoteiristaCirleneNiza:
    """Agente Roteirista v2b — CSMEA + hook_technique + kling_motion_prompt."""

    def __init__(self):
        self.gemini = MiniMaxClient()
        self.name = "Roteirista"
        self.role = (
            "Escritor de roteiros para vídeos de saúde e bem-estar. "
            "Gera scripts com hook_technique, CSMEA e kling_motion_prompt prontos para Kling 3.0."
        )
        self.backstory = PERSONA_PROMPT
        self.goal = "Gerar roteiro engajante com hook forte e prompts Kling prontos para produção."

    def generate_script(self, topic: str, research: str, style_guide: str) -> dict:
        prompt = SCRIPT_PROMPT_TEMPLATE.format(
            topic=topic, research=research, style_guide=style_guide
        )
        result = self.gemini.generate(
            prompt,
            system=PERSONA_PROMPT,
            temperature=0.8,
            max_tokens=8192,
        )
        return self._parse_script(result)

    def _parse_script(self, raw: str) -> dict:
        intro, main, outro = "", "", ""
        lines = raw.split("\n")
        current = None
        buffer: list[str] = []

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
        prompts: list[dict] = []
        lines = main_section.split("\n")
        current_scene: str | None = None
        data: dict = {}
        field: str | None = None

        def flush():
            if current_scene:
                prompts.append({
                    "scene": current_scene,
                    "hook_technique": data.get("hook", "").strip(),
                    "locutor": data.get("locutor", "").strip(),
                    "camera": data.get("camera", "").strip(),
                    "kling_motion_prompt": data.get("kling", "").strip(),
                    "nota_visual": data.get("nota", "").strip(),
                    "lighting": data.get("lighting", "").strip(),
                    "atmosphere": data.get("atmosphere", "").strip(),
                    # legacy compat for criativo agent
                    "prompt": data.get("kling", "").strip(),
                })

        for line in lines:
            stripped = line.strip()
            # scene header: ##Cena N: Título##
            if stripped.startswith("##Cena ") and stripped.endswith("##"):
                flush()
                current_scene = stripped.strip("#").strip()
                data = {}
                field = None
            elif stripped.startswith("HOOK:"):
                field = "hook"
                data["hook"] = stripped.replace("HOOK:", "").strip()
            elif stripped.startswith("LOCUTOR:"):
                field = "locutor"
                data["locutor"] = stripped.replace("LOCUTOR:", "").strip()
            elif stripped.upper().startswith("CAMERA:") or stripped.startswith("CÂMERA:"):
                field = "camera"
                data["camera"] = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("KLING PROMPT:"):
                field = "kling"
                data["kling"] = stripped.replace("KLING PROMPT:", "").strip()
            elif stripped.startswith("NOTA VISUAL:") or stripped.startswith("NOTA:"):
                field = "nota"
                data["nota"] = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("LIGHTING:"):
                field = "lighting"
                data["lighting"] = stripped.replace("LIGHTING:", "").strip()
            elif stripped.startswith("ATMOSPHERE:"):
                field = "atmosphere"
                data["atmosphere"] = stripped.replace("ATMOSPHERE:", "").strip()
            elif field and stripped and not stripped.startswith("##"):
                # continuation line
                data[field] = data.get(field, "") + " " + stripped

        flush()
        return prompts

    def apply_correction(self, current: dict, correction: str, step: str) -> dict:
        section_map = {
            "intro": ("INTRO", current.get("intro", "")),
            "main": ("MAIN", current.get("main", "")),
            "outro": ("OUTRO", current.get("outro", "")),
        }
        if step in section_map:
            label, content = section_map[step]
            prompt = (
                f"Ajusta o {label} conforme: {correction}\n\n"
                f"{label} ATUAL:\n{content}\n\n"
                f"Reescreve APENAS o {label}. Mantém formato v2b (HOOK/LOCUTOR/CAMERA/KLING PROMPT/NOTA VISUAL/LIGHTING/ATMOSPHERE)."
            )
        else:
            prompt = (
                f"Ajusta o roteiro completo conforme: {correction}\n\n"
                f"ROTEIRO:\n{current.get('full_script', '')}\n\n"
                f"Retorna roteiro completo com formato v2b."
            )
        result = self.gemini.generate(prompt, system=PERSONA_PROMPT, temperature=0.8)
        return self._parse_script(result)

    def generate_thumbnail_prompts(self, topic: str, style_guide: str) -> list[str]:
        prompt = f"""Generate 2 image generation prompts for a YouTube thumbnail about: {topic}

RULES:
- English only
- Visual elements only — no text, titles, words in image
- Concrete: food, ingredients, colors, lighting, composition
- Style: photorealistic, warm lighting, professional food/lifestyle photography
- Colors: warm terracotta, orange accents (#E07B39), clean background
- NO cartoon faces, NO people faces, NO abstract shapes
- Return exactly 2 prompts, each on its own line, no numbering, no labels

Now generate 2 prompts for: {topic}"""
        result = self.gemini.generate(prompt, temperature=0.6)
        return [
            line.strip()
            for line in result.strip().split("\n")
            if line.strip() and len(line.strip()) > 30
            and not line.strip()[0] in "#-*123456789"
            and not line.strip().startswith("Prompt")
        ][:2]

    def execute(self, topic: str, research: str, style_guide: str) -> dict:
        logger.info(f"Roteirista v2b: gerando roteiro para '{topic}'")
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
    roteirista = RoteiristaCirleneNiza()
    return Agent(
        name=roteirista.name,
        role=roteirista.role,
        backstory=roteirista.backstory,
        goal=roteirista.goal,
        tools=[],
        verbose=True,
    )
