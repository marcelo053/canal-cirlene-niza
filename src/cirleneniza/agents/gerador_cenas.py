from loguru import logger
from pathlib import Path
from cirleneniza.tools.fal import FalClient


class GeradorCenas:
    """Agente Gerador de Cenas — imagens 9:16 + Kling i2v com CSMEA prompt."""

    def __init__(self, fal_client=None):
        self.fal = fal_client or FalClient()
        self.name = "Gerador de Cenas"

    def generate_scene_images(
        self,
        cena_prompts: list[dict],
        style_context: str = "",
    ) -> list[dict]:
        """Generate 9:16 portrait image per scene using kling_motion_prompt (CSMEA).

        The KLING PROMPT describes subject+environment+lighting precisely.
        We strip motion/camera instructions (those are for Kling video, not image gen).
        """
        results = []
        for i, item in enumerate(cena_prompts):
            scene = item.get("scene", f"Cena {i+1}")

            # kling_motion_prompt contains full CSMEA — best visual description available
            kling_prompt = item.get("kling_motion_prompt") or item.get("prompt", "")
            # Strip Kling-specific terms not relevant for static image gen
            image_prompt = (
                kling_prompt
                .replace("Vertical 9:16.", "")
                .replace("Photorealistic.", "")
                .strip()
            )
            if style_context:
                image_prompt = f"{image_prompt}\n{style_context[:200]}"

            logger.info(f"GeradorCenas: imagem cena {i+1}/{len(cena_prompts)}: {scene[:50]}")
            result = self.fal.generate_image(
                prompt=image_prompt,
                model="fal-ai/flux/dev",
                aspect_ratio="9:16",
            )
            results.append({
                "scene_index": i,
                "scene_name": scene,
                "image_url": result["url"],
                "prompt": image_prompt,
                "kling_motion_prompt": kling_prompt,  # preserved for video gen
            })
        return results

    def generate_scene_videos(
        self,
        scene_images: list[dict],
        main_audio_duration: float,
    ) -> list[dict]:
        """Animate each scene image with Kling i2v using the CSMEA kling_motion_prompt."""
        videos = []
        num_scenes = len(scene_images)
        duration_per_scene = 5  # fixed 5s — narration drives final cut length

        for scene in scene_images:
            # MUST use kling_motion_prompt (CSMEA) not a generic fallback
            kling_prompt = scene.get("kling_motion_prompt") or scene.get("prompt", "")
            logger.info(
                f"GeradorCenas: video cena {scene['scene_index']+1}/{num_scenes}: "
                f"{scene.get('scene_name', '')[:40]}"
            )
            video = self.fal.generate_video(
                image_url=scene["image_url"],
                prompt=kling_prompt,
                duration=duration_per_scene,
                aspect_ratio="9:16",
            )
            videos.append({
                "scene_index": scene["scene_index"],
                "scene_name": scene.get("scene_name", ""),
                "video_url": video["url"],
                "duration": video["duration"],
                "kling_prompt": kling_prompt,
            })
            logger.info(f"GeradorCenas: cena {scene['scene_index']+1} -> {video['url']}")

        return videos

    def apply_correction(
        self,
        scene_index: int,
        correction: str,
        current_data: dict,
    ) -> dict:
        """Regenerate a specific scene image based on user correction."""
        logger.info(f"GeradorCenas: corrigindo cena {scene_index+1}: {correction}")
        cena_list = current_data.get("cena_prompts", [])
        current_kling = ""
        if scene_index < len(cena_list):
            current_kling = (
                cena_list[scene_index].get("kling_motion_prompt")
                or cena_list[scene_index].get("prompt", "")
            )
        new_prompt = f"{current_kling}\nCORRECAO: {correction}"

        result = self.fal.generate_image(
            prompt=new_prompt,
            aspect_ratio="9:16",
        )
        return {
            "scene_index": scene_index,
            "image_url": result["url"],
            "prompt": new_prompt,
            "kling_motion_prompt": new_prompt,
        }

    def execute(
        self,
        cena_prompts: list[dict],
        style_context: str = "",
        main_audio_duration: float = 120.0,
    ) -> dict:
        """Generate all scene images (9:16) then animate with Kling i2v (9:16)."""
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