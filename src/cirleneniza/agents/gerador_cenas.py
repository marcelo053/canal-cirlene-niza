from loguru import logger
from pathlib import Path
from cirleneniza.tools.fal import FalClient


class GeradorCenas:
    """Agente Gerador de Cenas — gera imagens e vídeos das cenas via fal.ai."""

    def __init__(self, fal_client=None):
        self.fal = fal_client or FalClient()
        self.name = "Gerador de Cenas"

    def generate_scene_images(
        self,
        cena_prompts: list[dict],
        style_context: str = "",
    ) -> list[dict]:
        """Generate image for each scene from cena_prompts."""
        results = []
        for i, item in enumerate(cena_prompts):
            scene = item.get("scene", f"Cena {i+1}")
            prompt = item.get("prompt", "")
            full_prompt = f"{prompt}\n{style_context}".strip()
            logger.info(f"GeradorCenas: gerand imagem cena {i+1}: {scene[:50]}")
            result = self.fal.generate_image(
                prompt=full_prompt,
                model="fal-ai/flux/dev",
                aspect_ratio="16:9",
            )
            results.append({
                "scene_index": i,
                "scene_name": scene,
                "image_url": result["url"],
                "prompt": full_prompt,
            })
        return results

    def generate_scene_videos(
        self,
        scene_images: list[dict],
        main_audio_duration: float,
    ) -> list[dict]:
        """Generate short video clip for each scene image."""
        videos = []
        num_scenes = len(scene_images)
        duration_per_scene = max(3, min(8, main_audio_duration / num_scenes))

        for scene in scene_images:
            video = self.fal.generate_video(
                image_url=scene["image_url"],
                prompt=f"Subtle motion, keep subject centered, cinematic",
                duration=int(duration_per_scene),
            )
            videos.append({
                "scene_index": scene["scene_index"],
                "scene_name": scene["scene_name"],
                "video_url": video["url"],
                "duration": video["duration"],
            })
            logger.info(f"GeradorCenas: cena {scene['scene_index']+1} video → {video['url']}")

        return videos

    def apply_correction(
        self,
        scene_index: int,
        correction: str,
        current_data: dict,
    ) -> dict:
        """Regenerate a specific scene based on correction."""
        logger.info(f"GeradorCenas: corrigindo cena {scene_index+1} → {correction}")
        current_prompt = current_data.get("cena_prompts", [{}])[scene_index].get("prompt", "")
        new_prompt = f"{current_prompt}\n\nCORREÇÃO: {correction}"

        result = self.fal.generate_image(
            prompt=new_prompt,
            aspect_ratio="16:9",
        )
        return {"scene_index": scene_index, "image_url": result["url"], "prompt": new_prompt}

    def execute(
        self,
        cena_prompts: list[dict],
        style_context: str = "",
        main_audio_duration: float = 120.0,
    ) -> dict:
        """Generate all scene images and videos."""
        logger.info(f"GeradorCenas: gerando {len(cena_prompts)} cenas")

        images = self.generate_scene_images(cena_prompts, style_context)

        video_segments = []
        if images:
            video_segments = self.generate_scene_videos(images, main_audio_duration)

        return {
            "scene_images": images,
            "scene_videos": video_segments,
            "status": "generated",
        }