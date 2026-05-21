from crewai import Agent
from loguru import logger
from pathlib import Path
from cirleneniza.tools.fal import FalClient


IDENTITY_PROMPTS = {
    "logo_cn_terracota": Path(__file__).parent.parent.parent / "identity" / "prompts" / "logo_cn_terracota.txt",
    "avatar_cn_badge": Path(__file__).parent.parent.parent / "identity" / "prompts" / "avatar_cn_badge.txt",
    "thumbnail_template": Path(__file__).parent.parent.parent / "identity" / "prompts" / "thumbnail_template.txt",
}


def load_prompt(prompt_name: str) -> str:
    """Load identity prompt from file."""
    path = IDENTITY_PROMPTS.get(prompt_name)
    if path and path.exists():
        return path.read_text()
    return f"Generate {prompt_name} for Canal Cirlene Niza health channel"


class DiretorDeArte:
    """Agente Diretor de Arte — logos, avatares, thumbnails via fal.ai."""

    def __init__(self, fal_client=None):
        self.fal = fal_client or FalClient()
        self.name = "Diretor de Arte"
        self.role = (
            "Diretor de arte especializado em branding para canal de saúde. "
            "Cria logos, avatares e thumbnails seguindo a identidade visual CN Terracota. "
            "Usa fal.ai Flux para geração de imagens."
        )
        self.backstory = (
            "Designer com experiência em identidade visual para canais de saúde e lifestyle. "
            "Conhece a paleta CN Terracota e sabe traduzir prompts em imagens profissionais."
        )
        self.goal = "Gerar assets visuais consistentes com a identidade do canal."

    def generate_logo(self, variant: str = "logo_cn_terracota") -> dict:
        """Gera logo principal CN Terracota."""
        prompt = load_prompt(variant)
        logger.info(f"Diretor de Arte: gerando {variant}")
        result = self.fal.generate(prompt, model="fal-ai/flux/dev", aspect_ratio="1:1")
        return {"logo_url": result["images"][0]["url"], "variant": variant}

    def generate_thumbnail(self, topic: str, prompt_override: str | None = None) -> dict:
        """Gera thumbnail para vídeo específico."""
        if prompt_override and len(prompt_override.strip()) > 30:
            # prompt concreto do roteirista — enriquecer com estilo visual fixo
            prompt = (
                f"{prompt_override.strip()}, "
                "warm terracotta color palette, orange accent tones, "
                "professional photography, sharp focus, vibrant, high contrast, "
                "no text, no words, no letters, no captions"
            )
        else:
            # fallback: prompt genérico baseado no tópico
            prompt = (
                f"Professional YouTube thumbnail photo about {topic}, "
                "food photography or lifestyle photography style, "
                "warm terracotta and orange color palette (#E07B39 accents), "
                "clean background, sharp focus, high contrast, inviting and vibrant, "
                "no text, no words, no letters, no captions, photorealistic"
            )
        logger.info(f"Diretor de Arte: gerando thumbnail para '{topic}'")
        logger.debug(f"Thumbnail prompt: {prompt[:120]}...")
        result = self.fal.generate(prompt, model="fal-ai/flux/schnell", aspect_ratio="16:9")
        return {"thumbnail_url": result["images"][0]["url"], "topic": topic}

    def execute(self, task: str, context: dict | None = None) -> dict:
        """Executa tarefa de arte."""
        logger.info(f"Diretor de Arte: executando '{task}'")
        if task == "logo":
            return self.generate_logo()
        elif task == "thumbnail":
            topic = context.get("topic", "") if context else ""
            thumbnail_prompt = context.get("thumbnail_prompt") if context else None
            return self.generate_thumbnail(topic, thumbnail_prompt)
        else:
            return {"error": f"Unknown task: {task}"}


def get_agent() -> Agent:
    """Factory para crewAI agent."""
    diretor = DiretorDeArte()
    return Agent(
        name=diretor.name,
        role=diretor.role,
        backstory=diretor.backstory,
        goal=diretor.goal,
        tools=[],
        verbose=True,
    )