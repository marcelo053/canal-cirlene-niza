import fal
from loguru import logger


class FalClient:
    """fal.ai client for image generation (logo, avatar, thumbnail)."""

    def __init__(self):
        settings = __import__("cirleneniza.config", fromlist=["get_settings"]).get_settings()
        fal.settings.API_TOKEN = settings.fal_api_key

    def generate(
        self,
        prompt: str,
        model: str = "fal-ai/flux/dev",
        aspect_ratio: str = "1:1",
    ) -> dict:
        """Generate image via fal.ai Flux."""
        result = fal.subscribe(
            "fal-ai/flux/dev",
            with_fields={
                "prompt": prompt,
                "image_size": {"width": 1024, "height": 1024},
                "num_images": 1,
            },
            sync=True,
        )
        return result
