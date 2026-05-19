import os
import fal_client
from loguru import logger


class FalClient:
    """fal.ai client for image generation (logo, avatar, thumbnail)."""

    def __init__(self):
        from cirleneniza.config import get_settings
        settings = get_settings()
        os.environ["FAL_KEY"] = settings.fal_api_key

    def generate(
        self,
        prompt: str,
        model: str = "fal-ai/flux/dev",
        aspect_ratio: str = "1:1",
    ) -> dict:
        """Generate image via fal.ai Flux."""
        result = fal_client.subscribe(
            model,
            arguments={
                "prompt": prompt,
                "image_size": {"width": 1024, "height": 1024},
                "num_images": 1,
            },
        )
        return result
