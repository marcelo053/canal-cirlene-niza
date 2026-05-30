from crewai import Agent
from loguru import logger
import re
from cirleneniza.tools.minimax import MiniMaxClient



def _sanitize(text: str) -> str:
    """Remove CJK/non-Portuguese unicode artifacts from MiniMax M2.7 output."""
    cleaned = re.sub(
        r"[\u3000-\u9fff\u3040-\u30ff\uf900-\ufaff\ufe30-\ufe4f]+",
        "",
        text,
    )
    cleaned = re.sub(r"  +", " ", cleaned)
    return cleaned.strip()

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
MÍNIMO OBRIGATÓRIO: 6 cenas. Ideal: 7-8 cenas.
Formato EXATO por cena (use exatamente estes marcadores):

##Cena N: [Título]##
HOOK: [myth_break | immediate_benefit | counter_intuitive | mirror_question] (SOMENTE NA CENA 1, vazio nas demais)
LOCUTOR: [MAX 35 palavras — veja regras de naturalidade abaixo]
CAMERA: [tipo: close-up / medium-shot / wide-shot] + [movimento: static / slow-zoom-in / slow-pan-right / slow-pan-left / handheld]
KLING PROMPT: [Camera movement]. [Subject described precisely]. [Action/movement]. [Environment]. [Lighting]. [Atmosphere]. Vertical 9:16. Photorealistic.
NOTA VISUAL: [descrição concreta do que aparece na tela]
LIGHTING: [soft natural light | golden hour | studio warm | outdoor bright]
ATMOSPHERE: [warm | energetic | calm | inspiring | cozy]

**NATURALIDADE DO LOCUTOR — regras obrigatórias:**
- Use `...` para pausas dramáticas antes de dados impactantes (ex: "Em apenas... 30 dias.")
- 1 cena no MEIO deve ter CTA orgânico integrado: "salva esse vídeo", "manda pra quem precisa ver"
- 1 cena deve ter pergunta reflexiva ao público: "você já sabia disso?", "faz sentido pra você?"
- Varie o ritmo: alterne cenas curtas (1 frase) com cenas de 2 frases
- Interjeições permitidas: "Olha só.", "Sabe o que é incrível?", "E o melhor:"
- NUNCA soe como manual técnico — soe como amiga contando descoberta importante

**KLING PROMPT deve seguir CSMEA em inglês com movimento obrigatório:**
Camera (C): tipo e movimento da câmera — SEMPRE inclua movimento (never "static" sozinho)
Subject (S): sujeito principal descrito com precisão visual
Movement (M): ação acontecendo — alimentos, líquidos, partículas SEMPRE em movimento
Environment (E): ambiente/cenário com detalhes de profundidade
Atmosphere (A): lighting + mood específicos

**OUTRO** — Cirlene em frente a câmera. MAX 40 palavras.
Agradecimento + convite para seguir. Tom: caloroso, 1ª pessoa.

DURAÇÃO: 2-3 minutos
- Intro: 15-20s
- Main: 90s-2min (6-8 cenas)
- Outro: 15-20s

## EXEMPLO DE CENAS CORRETAS (siga este padrão exato)

##Cena 1: O mito que te sabota##
HOOK: myth_break
LOCUTOR: Todo mundo diz que proteína engorda. A ciência prova o contrário... e muda tudo o que você pensava sobre emagrecer.
CAMERA: close-up + slow-zoom-in
KLING PROMPT: Extreme close-up shot, slow zoom in. Whey protein powder falling in slow motion into a glass shaker filled with clear water. Powder cloud swirling and dissolving in beautiful spirals. Bright modern kitchen counter, soft morning light streaming through window. Warm golden tones, clean aesthetic. Inspiring, empowering atmosphere. Vertical 9:16. Photorealistic.
NOTA VISUAL: Pó de whey caindo em câmera lenta em coqueteleira, nuvem se dissolvendo em espirais.
LIGHTING: soft natural light
ATMOSPHERE: inspiring

##Cena 2: Absorção que surpreende##
HOOK:
LOCUTOR: Em... 30 minutos. É o tempo que leva para o whey chegar ao músculo. Nenhum outro alimento age tão rápido.
CAMERA: medium-shot + slow-pan-right
KLING PROMPT: Medium shot, slow pan right. Close-up of a stopwatch ticking, hands moving in real time. Glowing nutrient particles flowing from the watch face into a muscular forearm with veins subtly visible. Dark background with warm amber spot lighting. Energetic, scientific atmosphere. Vertical 9:16. Photorealistic.
NOTA VISUAL: Cronômetro marcando tempo com partículas luminosas fluindo para o músculo.
LIGHTING: studio warm
ATMOSPHERE: energetic

##Cena 4: Salva esse vídeo##
HOOK:
LOCUTOR: Salva esse vídeo — porque a maioria das pessoas descobre isso só depois de meses perdendo resultado por falta de proteína.
CAMERA: wide-shot + slow-zoom-in
KLING PROMPT: Wide shot, slow zoom in. Healthy meal prep containers arranged on a clean kitchen counter, colorful vegetables and protein foods visible. Woman's hands arranging containers with care. Warm afternoon light through kitchen window. Cozy, organized, motivating atmosphere. Vertical 9:16. Photorealistic.
NOTA VISUAL: Marmitas organizadas com refeições coloridas e saudáveis na bancada da cozinha.
LIGHTING: golden hour
ATMOSPHERE: warm

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

        intro = _sanitize(intro)
        main = _sanitize(main)
        outro = _sanitize(outro)

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
        try:
            thumbnail_prompts = self.generate_thumbnail_prompts(topic, style_guide)
        except Exception as e:
            logger.warning(f"Thumbnail prompts failed (skipping): {e}")
            thumbnail_prompts = []
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
