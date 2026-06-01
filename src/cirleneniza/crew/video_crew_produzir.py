import subprocess
import uuid
from pathlib import Path
from loguru import logger

from cirleneniza.agents.narrador import Narrador
from cirleneniza.agents.editor_audio import EditorAudio
from cirleneniza.agents.gerador_cenas import GeradorCenas
from cirleneniza.agents.gerador_prompts import GeradorDePrompts
from cirleneniza.agents.gerador_slides import GeradorSlidesCientificos
from cirleneniza.agents.editor_video import EditorVideo
from cirleneniza.agents.publicador import Publicador
from cirleneniza.tools.heygen import HeyGenClient
from cirleneniza.tools.minio import MinIOClient
from cirleneniza.tools.fal import FalClient
from cirleneniza.tools.nca_toolkit import NCAToolkitClient
from cirleneniza.tools.baserow import BaserowClient
from cirleneniza.tools.cost_tracker import CostTracker
from cirleneniza.config import get_settings



def _extract_locutor_lines(main_section: str) -> str:
    """Extract only LOCUTOR narration lines from MAIN section for ElevenLabs TTS.

    The MAIN section contains structured fields (HOOK, CAMERA, KLING PROMPT, etc.)
    that must NOT be sent to TTS. This extracts only the actual narration text.
    """
    lines = []
    for line in main_section.split("\n"):
        stripped = line.strip()
        if stripped.startswith("LOCUTOR:"):
            text = stripped.replace("LOCUTOR:", "").strip()
            if text:
                lines.append(text)
    return " ".join(lines)


class ProduzirCrew:
    """Pipeline de produção — fases 4-10 após aprovação."""

    def __init__(self):
        cfg = get_settings()
        self.narrador = Narrador()
        self.editor_audio = EditorAudio()
        self.gerador_cenas = GeradorCenas()
        self.gerador_prompts = GeradorDePrompts()
        self.editor_video = EditorVideo(nca=NCAToolkitClient(cfg.nca_toolkit_url, api_key=cfg.nca_api_key))
        self.gerador_slides = GeradorSlidesCientificos(minio=self.minio)
        self.publicador = Publicador()
        self.minio = MinIOClient(
            endpoint=cfg.minio_endpoint.removeprefix("http://"),
            access_key=cfg.minio_access_key,
            secret_key=cfg.minio_secret_key,
            bucket_work=cfg.minio_bucket_work,
            bucket_final=cfg.minio_bucket_final,
            public_endpoint=cfg.minio_public_endpoint or None,
        )
        self.heygen = HeyGenClient(
            api_key=cfg.heygen_api_key,
            talking_photo_id=cfg.heygen_talking_photo_id,
        )
        self.baserow = BaserowClient(
            base_url=cfg.baserow_url,
            token=cfg.baserow_token,
        )
        self.tracker = CostTracker(self.baserow, cfg.baserow_table_costs)
        self._cfg = cfg

    def run(self, session: dict) -> dict:
        """Executa produção completa após aprovação do roteiro."""
        sd = session.get("script_data", {})
        topic = session.get("topic", "")
        production_id = session.get("production_id")

        logger.info(f"ProduzirCrew: iniciando produção para '{topic}'")

        if not production_id:
            prod_row = self.baserow.create_row(self._cfg.baserow_table_productions, {
                "title": topic,
                "status": "em_producao",
            })
            production_id = prod_row["id"]
            session["production_id"] = production_id

        result = {
            "production_id": production_id,
            "topic": topic,
            "status": "in_progress",
        }

        # === FASE 4: Narrador — 3 áudios separados ===
        logger.info("Fase 4: Narrador — gerando áudios")
        audio_intro = self.narrador.execute(sd["intro"], production_id)
        main_narration = _extract_locutor_lines(sd.get("main", ""))
        audio_main = self.narrador.execute(main_narration, production_id)
        audio_outro = self.narrador.execute(sd["outro"], production_id)

        main_duration = audio_main.get("duration_estimate_sec", 120)
        result["audios"] = {
            "intro": audio_intro["audio_path"],
            "main": audio_main["audio_path"],
            "outro": audio_outro["audio_path"],
        }
        total_chars = len(sd.get("intro", "")) + len(main_narration) + len(sd.get("outro", ""))
        self.tracker.log_elevenlabs(production_id, total_chars, "narração intro+main+outro")

        # === FASE 5: EditorAudio — normaliza 3 áudios ===
        logger.info("Fase 5: EditorAudio — normalizando áudios")
        norm_intro = Path(self.editor_audio.execute(audio_intro["audio_path"], normalize=True)["audio_path"])
        norm_main = Path(self.editor_audio.execute(audio_main["audio_path"], normalize=True)["audio_path"])
        norm_outro = Path(self.editor_audio.execute(audio_outro["audio_path"], normalize=True)["audio_path"])

        result["normalized_paths"] = {
            "intro": str(norm_intro),
            "main": str(norm_main),
            "outro": str(norm_outro),
        }

        # Concat full narration audio: intro + main + outro
        combined_audio = self._concat_audio(
            [norm_intro, norm_main, norm_outro],
            output=Path(f"/tmp/cirlene_{production_id}_audio_full.m4a"),
        )
        result["combined_audio"] = str(combined_audio)

        # === FASE 5.5: GeradorDePrompts — enriquece cena_prompts com Kling 3.0 CSMEA ===
        logger.info("Fase 5.5: GeradorDePrompts — enriquecendo KLING PROMPTS")
        raw_cena_prompts = sd.get("cena_prompts", [])
        cena_prompts_enriched = self.gerador_prompts.enrich(raw_cena_prompts) if raw_cena_prompts else []

        # === FASE 6: GeradorCenas — gera imagens e vídeos das cenas ===
        cena_prompts = cena_prompts_enriched
        style_context = session.get("style_guide", "")[:500]

        logger.info(f"Fase 6: GeradorCenas — gerando {len(cena_prompts)} cenas")
        cenas_result = self.gerador_cenas.execute(
            cena_prompts=cena_prompts,
            style_context=style_context,
            main_audio_duration=main_duration,
        )
        scene_videos = cenas_result.get("scene_videos", [])
        scene_images = cenas_result.get("scene_images", [])
        result["cenas"] = {
            "images": scene_images,
            "videos": scene_videos,
        }
        n_imgs = len(scene_images)
        n_vids = len(scene_videos)
        if n_imgs:
            self.tracker.log_fal_image(production_id, n_imgs, "cenas Flux 9:16")
        if n_vids:
            self.tracker.log_fal_video(production_id, n_vids, 5, "cenas Kling i2v")

        # === FASE 6.5: GeradorSlidesCientificos — slides Remotion (assets independentes) ===
        slide_urls: list[str] = []
        try:
            research = session.get("research", "")
            if research:
                logger.info("Fase 6.5: GeradorSlides — renderizando slides científicos")
                slides_result = self.gerador_slides.execute(
                    research=research,
                    topic=topic,
                    production_id=production_id,
                )
                slide_urls = slides_result.get("slide_urls", [])
                result["slide_urls"] = slide_urls
                logger.info(f"Fase 6.5: {len(slide_urls)} slides gerados")
            else:
                logger.warning("Fase 6.5: sem research disponível — slides ignorados")
        except Exception as e:
            logger.warning(f"Fase 6.5: slides falharam (pipeline continua): {e}")

        # === FASE 7: HeyGen — avatar intro + avatar outro ===
        logger.info("Fase 7: HeyGen — avatar intro + outro")
        asset_intro = self.heygen.upload_audio(norm_intro)
        video_intro_id = self.heygen.generate_video(audio_asset_id=asset_intro)
        video_intro_url = self.heygen.wait_for_completion(video_intro_id)
        logger.info(f"HeyGen intro: {video_intro_url}")

        asset_outro = self.heygen.upload_audio(norm_outro)
        video_outro_id = self.heygen.generate_video(audio_asset_id=asset_outro)
        video_outro_url = self.heygen.wait_for_completion(video_outro_id)
        logger.info(f"HeyGen outro: {video_outro_url}")

        local_intro = Path(f"/tmp/cirlene_{production_id}_intro.mp4")
        local_outro = Path(f"/tmp/cirlene_{production_id}_outro.mp4")
        self.heygen.download_video(video_intro_url, local_intro)
        self.heygen.download_video(video_outro_url, local_outro)
        self.tracker.log_heygen(production_id, 2, "avatar intro + outro")

        # === FASE 8: EditorVideo — FFmpeg: intro + cenas + main + outro ===
        logger.info("Fase 8: EditorVideo — compondo vídeo final")

        all_videos = [str(local_intro)]
        video_urls = [v["video_url"] for v in scene_videos]
        num_scenes = len(video_urls)

        # Extend each scene to cover its share of main_duration so combined
        # audio (intro+main+outro) stays in sync with total video duration.
        scene_target_sec = (main_duration / num_scenes) if num_scenes else 5.0

        scene_clips: list[Path] = []
        for i, v_url in enumerate(video_urls):
            local_clip = Path(f"/tmp/cirlene_{production_id}_scene_{uuid.uuid4().hex[:6]}.mp4")
            self._download_url(v_url, local_clip)
            extended = Path(f"/tmp/cirlene_{production_id}_scene_ext_{i}.mp4")
            self._extend_video(local_clip, extended, scene_target_sec)
            local_clip.unlink(missing_ok=True)
            scene_clips.append(extended)
            all_videos.append(str(extended))

        all_videos.append(str(local_outro))

        final_video = self.editor_video.compose_from_segments(
            video_paths=all_videos,
            main_audio=str(combined_audio),
            output=Path(f"/tmp/cirlene_{production_id}_final.mp4"),
        )

        # === FASE 9: NCA Toolkit — legendas (opcional) ===
        srt_path = None
        try:
            logger.info("Fase 9: NCA Toolkit — gerando legendas via URL MinIO")
            # NCA Toolkit requires public URL (not local path)
            audio_minio_key = f"productions/{production_id}/main_narration.mp3"
            self.minio.upload_file(str(norm_main), self.minio.bucket_work, audio_minio_key)
            audio_public_url = self.minio.generate_presigned_url(self.minio.bucket_work, audio_minio_key)
            from cirleneniza.tools.nca_toolkit import NCAToolkitClient as _NCA
            nca = _NCA(self._cfg.nca_toolkit_url, api_key=self._cfg.nca_api_key)
            srt_text = nca.generate_captions_srt(audio_public_url, language="pt")
            if srt_text:
                srt_path = Path(f"/tmp/cirlene_{production_id}_main.srt")
                srt_path.write_text(srt_text, encoding="utf-8")
                logger.info(f"Fase 9: SRT gerado → {srt_path} ({len(srt_text)} chars)")
        except Exception as e:
            logger.warning(f"Legendas NCA falharam (ignorando): {e}")

        # === FASE 10: Publicador ===
        logger.info("Fase 10: Publicador — publicando")
        pub_result = self.publicador.execute(
            video_path=str(final_video),
            production_id=production_id,
            title=topic,
            description=(sd.get("main") or "")[:500],
            tags="saude,bemestar,cirleneniza",
        )

        result["status"] = "published"
        result["video_url"] = pub_result.get("video_url")
        result["post_ids"] = pub_result.get("post_ids")
        result["slide_urls"] = slide_urls

        # Cleanup
        cleanup_paths = [local_intro, local_outro, final_video, norm_intro, norm_main, norm_outro, combined_audio, *scene_clips]
        if srt_path:
            cleanup_paths.append(srt_path)
        for p in cleanup_paths:
            try:
                Path(p).unlink(missing_ok=True)
            except Exception:
                pass

        logger.info(f"ProduzirCrew: concluído production_id={production_id}")
        return result

    def _extend_video(self, src: Path, dst: Path, target_sec: float) -> Path:
        """Loop src video to fill target_sec duration, re-encoding for clean cut."""
        dst.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            ["ffmpeg", "-y", "-stream_loop", "-1", "-i", str(src),
             "-t", str(round(target_sec, 3)),
             "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an",
             str(dst)],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            logger.warning(f"_extend_video failed ({result.stderr[-200:]}), using original")
            import shutil
            shutil.copy(src, dst)
        return dst

    def _concat_audio(self, audio_paths: list[Path], output: Path) -> Path:
        output.parent.mkdir(parents=True, exist_ok=True)
        inputs = []
        for p in audio_paths:
            inputs.extend(["-i", str(Path(p).resolve())])
        n = len(audio_paths)
        filter_complex = "".join(f"[{i}:a]" for i in range(n)) + f"concat=n={n}:v=0:a=1[out]"
        result = subprocess.run(
            ["ffmpeg", "-y", *inputs,
             "-filter_complex", filter_complex,
             "-map", "[out]", "-c:a", "aac", str(output)],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg concat audio failed: {result.stderr[-500:]}")
        logger.info(f"ProduzirCrew: áudio concat → {output}")
        return output

    def _download_url(self, url: str, path: Path) -> Path:
        import requests
        path.parent.mkdir(parents=True, exist_ok=True)
        resp = requests.get(url, stream=True, timeout=120)
        resp.raise_for_status()
        with open(path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        return path