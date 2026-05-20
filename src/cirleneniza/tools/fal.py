import os
import fal_client
from loguru import logger
from pathlib import Path


class FalClient:
    """fal.ai client for image and video generation."""

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

    def generate_image(
        self,
        prompt: str,
        model: str = "fal-ai/flux/dev",
        aspect_ratio: str = "1:1",
    ) -> dict:
        """Generate single image, return URL."""
        result = self.generate(prompt, model, aspect_ratio)
        return {"url": result["images"][0]["url"], "prompt": prompt}

    def generate_video(
        self,
        image_url: str,
        prompt: str,
        model: str = "fal-ai/kling-video/v2.5-turbo/standard/image-to-video",
        duration: int = 5,
    ) -> dict:
        """Generate video from image using kling-video i2v."""
        result = fal_client.subscribe(
            model,
            arguments={
                "prompt": prompt,
                "image_url": image_url,
                "duration": str(duration),
            },
            timeout=300,
        )
        video_url = result["video"]["url"]
        logger.info(f"FalClient: video generated → {video_url}")
        return {"url": video_url, "duration": duration}

    def generate_scene_videos(
        self,
        scene_images: list[dict],
        style_context: str = "",
    ) -> list[dict]:
        """Generate videos for multiple scenes. scene_images = [{prompt, image_url}, ...]"""
        videos = []
        for i, scene in enumerate(scene_images):
            logger.info(f"FalClient: generating scene {i+1}/{len(scene_images)}")
            video = self.generate_video(
                image_url=scene["image_url"],
                prompt=scene["prompt"],
            )
            videos.append({
                "scene_index": i,
                "video_url": video["url"],
                "duration": video["duration"],
                "scene_prompt": scene["prompt"],
            })
        return videos

    def download_file(self, url: str, output_path: Path | str) -> Path:
        """Download generated file to local path."""
        import requests
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        resp = requests.get(url, stream=True, timeout=120)
        resp.raise_for_status()
        with open(output_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        logger.info(f"FalClient: downloaded → {output_path}")
        return output_path
