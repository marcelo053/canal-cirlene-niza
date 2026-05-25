import os
import fal_client
from loguru import logger
from pathlib import Path


# Portrait dimensions for 9:16 vertical video (TikTok/Reels/Shorts)
_ASPECT_SIZES = {
    "9:16": {"width": 576, "height": 1024},
    "16:9": {"width": 1024, "height": 576},
    "1:1":  {"width": 1024, "height": 1024},
    "4:5":  {"width": 820, "height": 1024},
}


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
        aspect_ratio: str = "9:16",
    ) -> dict:
        """Generate image via fal.ai Flux with correct portrait dimensions."""
        size = _ASPECT_SIZES.get(aspect_ratio, _ASPECT_SIZES["9:16"])
        result = fal_client.subscribe(
            model,
            arguments={
                "prompt": prompt,
                "image_size": size,
                "num_images": 1,
            },
        )
        return result

    def generate_image(
        self,
        prompt: str,
        model: str = "fal-ai/flux/dev",
        aspect_ratio: str = "9:16",
    ) -> dict:
        """Generate single portrait image (9:16), return URL."""
        result = self.generate(prompt, model, aspect_ratio)
        return {"url": result["images"][0]["url"], "prompt": prompt}

    def generate_video(
        self,
        image_url: str,
        prompt: str,
        model: str = "fal-ai/kling-video/v2.5-turbo/standard/image-to-video",
        duration: int = 5,
        aspect_ratio: str = "9:16",
    ) -> dict:
        """Generate video from image using Kling i2v.

        aspect_ratio: '9:16' for vertical (TikTok/Reels/Shorts default).
        duration: 5 or 10 seconds.
        """
        valid_duration = "10" if duration > 5 else "5"
        result = fal_client.subscribe(
            model,
            arguments={
                "prompt": prompt,
                "image_url": image_url,
                "duration": valid_duration,
                "aspect_ratio": aspect_ratio,
            },
            client_timeout=300,
        )
        video_url = result["video"]["url"]
        logger.info(f"FalClient: video {aspect_ratio} {valid_duration}s -> {video_url}")
        return {"url": video_url, "duration": int(valid_duration)}

    def generate_scene_videos(
        self,
        scene_images: list[dict],
        style_context: str = "",
    ) -> list[dict]:
        """Generate videos for multiple scenes.

        scene_images items must include 'kling_motion_prompt' (or fallback 'prompt').
        Uses 9:16 portrait aspect for all clips.
        """
        videos = []
        for i, scene in enumerate(scene_images):
            logger.info(f"FalClient: generating scene {i+1}/{len(scene_images)}")
            kling_prompt = scene.get("kling_motion_prompt") or scene.get("prompt", "")
            video = self.generate_video(
                image_url=scene["image_url"],
                prompt=kling_prompt,
                aspect_ratio="9:16",
            )
            videos.append({
                "scene_index": i,
                "video_url": video["url"],
                "duration": video["duration"],
                "scene_prompt": kling_prompt,
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
        logger.info(f"FalClient: downloaded -> {output_path}")
        return output_path
