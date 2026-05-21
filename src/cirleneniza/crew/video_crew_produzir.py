import uuid
from pathlib import Path
from loguru import logger

from cirleneniza.agents.narrador import Narrador
from cirleneniza.agents.editor_audio import EditorAudio
from cirleneniza.agents.gerador_cenas import GeradorCenas
from cirleneniza.agents.editor_video import EditorVideo
from cirleneniza.agents.publicador import Publicador
from cirleneniza.tools.heygen import HeyGenClient
from cirleneniza.tools.minio import MinIOClient
from cirleneniza.tools.fal import FalClient
from cirleneniza.tools.nca_toolkit import NCAToolkitClient
from cirleneniza.tools.baserow import BaserowClient
from cirleneniza.config import get_settings


class ProduzirCrew:
    """Pipeline de produção — fases 4-10 após aprovação."""

    def __init__(self):
        cfg = get_settings()
        self.narrador = Narrador()
        self.editor_audio = EditorAudio()
        self.gerador_cenas = GeradorCenas()
        self.editor_video = EditorVideo(nca=NCAToolkitClient(cfg.nca_toolkit_url))
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
        audio_main = self.narrador.execute(sd["main"], production_id)
        audio_outro = self.narrador.execute(sd["outro"], production_id)

        main_duration = audio_main.get("duration_estimate_sec", 120)
        result["audios"] = {
            "intro": audio_intro["audio_path"],
            "main": audio_main["audio_path"],
            "outro": audio_outro["audio_path"],
        }

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

        # === FASE 6: GeradorCenas — gera imagens e vídeos das cenas ===
        cena_prompts = sd.get("cena_prompts", [])
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

        # === FASE 8: EditorVideo — FFmpeg: intro + cenas + main + outro ===
        logger.info("Fase 8: EditorVideo — compondo vídeo final")

        all_videos = [str(local_intro)]
        video_urls = [v["video_url"] for v in scene_videos]

        for v_url in video_urls:
            local_clip = Path(f"/tmp/cirlene_{production_id}_scene_{uuid.uuid4().hex[:6]}.mp4")
            self._download_url(v_url, local_clip)
            all_videos.append(str(local_clip))

        all_videos.append(str(local_outro))

        final_video = self.editor_video.compose_from_segments(
            video_paths=all_videos,
            main_audio=str(norm_main),
            output=Path(f"/tmp/cirlene_{production_id}_final.mp4"),
        )

        # === FASE 9: NCA Toolkit — legendas (opcional) ===
        srt_path = None
        try:
            logger.info("Fase 9: NCA Toolkit — gerando legendas")
            srt_path = self.editor_video.generate_srt(str(norm_main))
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

        # Cleanup
        cleanup_paths = [local_intro, local_outro, final_video, norm_intro, norm_main, norm_outro]
        if srt_path:
            cleanup_paths.append(srt_path)
        for p in cleanup_paths:
            try:
                Path(p).unlink(missing_ok=True)
            except Exception:
                pass

        logger.info(f"ProduzirCrew: concluído production_id={production_id}")
        return result

    def _download_url(self, url: str, path: Path) -> Path:
        import requests
        path.parent.mkdir(parents=True, exist_ok=True)
        resp = requests.get(url, stream=True, timeout=120)
        resp.raise_for_status()
        with open(path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        return path