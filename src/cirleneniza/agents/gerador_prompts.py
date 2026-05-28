"""GeradorDePrompts — enriquece cena_prompts com KLING PROMPTS otimizados para Kling 3.0.

Conhecimento base extraído do NotebookLM:
  "Kling AI & Engenharia de Prompt para Vídeo — Canal Cirlene Niza"
  Notebook ID: d7550e5e-c453-4b9a-afaa-f0a667d6f20f
"""
from loguru import logger
from cirleneniza.tools.minimax import MiniMaxClient


_SYSTEM = """You are an expert Kling AI 3.0 prompt engineer for Canal Cirlene Niza health content.

## CANAL CIRLENE NIZA — BRAND VOICE & VISUAL IDENTITY

**Persona**: Cirlene — Brazilian woman in her 40s, curly hair, warm smile. Nutritionist.
Tone: welcoming, practical, empowering. NOT alarmist. NOT excessive technical jargon.
Keywords: saúde, equilíbrio, transformação, hábitos, consistência, bem-estar.

**Visual Identity**:
- Palette: warm greens, whites, beige, coral/orange accents (#E07B39)
- Style: clean, modern, welcoming, soft natural light
- Elements: fresh food, clean kitchens, natural ingredients
- AVOID: aggressive colors, gym aesthetics, text overlay, artificial look, shaky camera

**Format**: Always vertical 9:16 (TikTok/Reels/Shorts)

---

## KLING 3.0 CSMEA FORMULA

Structure: [Camera/Shot type + movement]. [Subject precisely described]. [Action/movement happening].
           [Environment with depth]. [Lighting]. [Atmosphere/mood]. Vertical 9:16. Photorealistic. Cinematic 4K.

### TEMPLATES BY SCENE TYPE:

**HOOK** — captures attention in first 3 seconds (myth_break / counter_intuitive / immediate_benefit / mirror_question)
> Close-up of a Brazilian woman in her 40s with curly hair and a warm smile (Cirlene), looking directly into
> the camera with excitement, eyebrows raised. Camera zooms in slowly to her face. Clean bright modern kitchen
> background, soft natural light streaming from the side. Vibrant colors, welcoming atmosphere.
> Vertical 9:16. Photorealistic. Cinematic 4K.

**INFORMATIVE** — delivering nutrition tip or data point
> Medium shot of Cirlene (Brazilian woman, 40s, curly hair, warm smile) gesturing expressively with her hands
> while explaining a nutrition tip. Steady camera with a slight handheld feel for authenticity. Background shows
> a minimalist shelf with healthy ingredients and warm lighting. Shallow depth of field (bokeh background).
> High-quality broadcast style, motivating tone. Vertical 9:16. Photorealistic. Cinematic 4K.

**FOOD B-ROLL** — ingredient or superfood highlight (no Cirlene in frame)
> Extreme close-up macro shot of fresh [INGREDIENT] being poured / cut / mixed, creating a swirling / flowing
> motion. Slow motion (120fps feel). Golden hour warm light hitting the surface and liquid droplets.
> Natural green and beige palette, hyper-detailed texture. Fresh and appetizing atmosphere.
> Vertical 9:16. Photorealistic. Cinematic 4K.

**CTA** — call to action scene (salva, segue, compartilha, manda pra)
> Medium shot of Cirlene (Brazilian woman, 40s, curly hair) facing the camera with a confident and friendly
> smile, nodding encouragingly toward the viewer. Steady stable camera. Clean background with soft warm rim
> lighting. Professional color grading, empowering and personal atmosphere.
> Vertical 9:16. Photorealistic. Cinematic 4K.

---

## KLING 3.0 ADVANCED RULES

1. Always write in English
2. Food/liquids ALWAYS in motion — use: pour, swirl, dissolve, drip, slice, flow, steam. NEVER static food.
3. Camera ALWAYS has movement unless it is a CTA scene — use: slow zoom in, slow pan right/left, tracking shot, handheld
4. For Cirlene scenes always use: "Brazilian woman in her 40s with curly hair and warm smile"
5. End every prompt with: Vertical 9:16. Photorealistic. Cinematic 4K.
6. Negative guidance (append when appropriate): no text, no watermarks, no shaky camera, no artificial look
7. Kling 3.0 Element Reference note (internal): use consistent Cirlene description across all scenes for character continuity

## SCENE TYPE DETECTION

- HOOK → hook_technique field is NOT empty (myth_break / immediate_benefit / counter_intuitive / mirror_question)
- CTA → locutor contains any of: salva, segue, compartilha, manda pra, curte, comenta
- FOOD B-ROLL → nota_visual describes food/ingredient without Cirlene; or locutor describes data without talking head
- INFORMATIVE → all other scenes (default)

## OUTPUT FORMAT

After your internal reasoning, output EXACTLY this structure:
KLING_PROMPT_START
[the complete CSMEA prompt here — nothing else]
KLING_PROMPT_END
"""

_QUERY = """\
Generate an optimized Kling AI 3.0 CSMEA prompt for this Canal Cirlene Niza scene:

Scene title: {scene}
Hook technique: {hook_technique}
Narration (LOCUTOR): {locutor}
Visual note (NOTA VISUAL): {nota_visual}
Camera suggestion: {camera}
Lighting: {lighting}
Atmosphere: {atmosphere}

Detect the scene type, apply the correct template.
Output format (mandatory):
KLING_PROMPT_START
[your complete CSMEA prompt here]
KLING_PROMPT_END
"""


class GeradorDePrompts:
    """Enriquece cena_prompts com KLING PROMPTS otimizados para Kling 3.0.

    Usa MiniMax com conhecimento extraído do NotebookLM Canal Cirlene Niza.
    Chamado entre Roteirista e GeradorCenas no pipeline de produção.
    """

    def __init__(self):
        self.llm = MiniMaxClient()
        self.name = "Gerador de Prompts"

    def enrich_scene(self, scene: dict) -> dict:
        """Gera KLING PROMPT otimizado para uma cena e retorna scene atualizado."""
        prompt = _QUERY.format(
            scene=scene.get("scene", ""),
            hook_technique=scene.get("hook_technique", ""),
            locutor=scene.get("locutor", ""),
            nota_visual=scene.get("nota_visual", ""),
            camera=scene.get("camera", ""),
            lighting=scene.get("lighting", ""),
            atmosphere=scene.get("atmosphere", ""),
        )
        try:
            raw = self.llm.generate(
                prompt=prompt,
                system=_SYSTEM,
                temperature=0.7,
                max_tokens=1024,
            ).strip()
            # Extract between markers (M2.7 reasons out loud before the actual prompt)
            kling_prompt = self._extract_prompt(raw)
            # Safety: ensure ends with required tags
            if "Vertical 9:16" not in kling_prompt:
                kling_prompt += " Vertical 9:16. Photorealistic. Cinematic 4K."
            updated = dict(scene)
            updated["kling_motion_prompt"] = kling_prompt
            updated["prompt"] = kling_prompt  # legacy compat
            logger.info(
                f"GeradorDePrompts: cena '{scene.get('scene', '')[:40]}' → "
                f"{len(kling_prompt)} chars"
            )
            return updated
        except Exception as e:
            logger.warning(f"GeradorDePrompts: erro na cena '{scene.get('scene', '')}': {e} — mantendo original")
            return scene

    @staticmethod
    def _extract_prompt(raw: str) -> str:
        """Extract KLING PROMPT between markers. Falls back to last camera-term paragraph."""
        start_tag = "KLING_PROMPT_START"
        end_tag = "KLING_PROMPT_END"

        # Strip markers from raw so fallback doesn't include them
        clean = raw.replace(start_tag, "").replace(end_tag, "")

        if start_tag in raw and end_tag in raw:
            inner = raw.split(start_tag, 1)[1].split(end_tag, 1)[0].strip()
            if inner and len(inner) > 60:
                return inner

        # Fallback: last paragraph containing camera/visual terms
        camera_terms = {"shot", "close-up", "medium", "wide", "camera", "zoom", "pan", "tracking",
                        "macro", "cinematic", "photorealistic", "vertical"}
        paragraphs = [p.strip() for p in clean.split("\n\n") if p.strip()]
        for para in reversed(paragraphs):
            if any(t in para.lower() for t in camera_terms) and len(para) > 80:
                return para

        # Last resort: last non-empty line
        lines = [l.strip() for l in clean.splitlines() if l.strip()]
        return lines[-1] if lines else raw

    def enrich(self, cena_prompts: list[dict]) -> list[dict]:
        """Enriquece todas as cenas. Falha individual não interrompe pipeline."""
        logger.info(f"GeradorDePrompts: enriquecendo {len(cena_prompts)} cenas")
        enriched = []
        for i, scene in enumerate(cena_prompts):
            logger.debug(f"GeradorDePrompts: cena {i+1}/{len(cena_prompts)}")
            enriched.append(self.enrich_scene(scene))
        logger.info("GeradorDePrompts: enriquecimento concluído")
        return enriched

    def execute(self, cena_prompts: list[dict]) -> list[dict]:
        """Alias público para enrich()."""
        return self.enrich(cena_prompts)
