import uuid
from pathlib import Path

from loguru import logger

from cirleneniza.agents.calendario import CalendarioEditorial
from cirleneniza.agents.roteirista import RoteiristaCirleneNiza
from cirleneniza.agents.revisor import RevisorEspecialista
from cirleneniza.agents.narrador import Narrador
from cirleneniza.agents.diretor_arte import DiretorDeArte
from cirleneniza.agents.editor_audio import EditorAudio
from cirleneniza.agents.publicador import Publicador
from cirleneniza.config import get_settings
from cirleneniza.tools.baserow import BaserowClient
from cirleneniza.tools.heygen import HeyGenClient
from cirleneniza.tools.minio import MinIOClient


class VideoCrew:
    """Pipeline Canal Cirlene Niza — execução direta via execute() de cada agente."""

    def __init__(self):
        self.calendario = CalendarioEditorial()
        self.roteirista = RoteiristaCirleneNiza()
        self.revisor = RevisorEspecialista()
        self.narrador = Narrador()
        self.diretor_arte = DiretorDeArte()
        self.editor_audio = EditorAudio()
        self.publicador = Publicador()
        cfg = get_settings()
        self.baserow = BaserowClient(
            base_url=cfg.baserow_url,
            token=cfg.baserow_token,
        )
        self.minio = MinIOClient(
            endpoint=cfg.minio_endpoint.removeprefix("http://"),
            access_key=cfg.minio_access_key,
            secret_key=cfg.minio_secret_key,
            bucket_work=cfg.minio_bucket_work,
            bucket_final=cfg.minio_bucket_final,
        )
        self.heygen = HeyGenClient(
            api_key=cfg.heygen_api_key,
            talking_photo_id=cfg.heygen_talking_photo_id,
        )
        self._cfg = cfg

    def run(self, topic: str) -> dict:
        """Executa pipeline completo: pesquisa → roteiro → narração → vídeo → publicação."""
        logger.info(f"VideoCrew: iniciando pipeline para '{topic}'")
        cfg = self._cfg

        # Registro inicial
        prod_row = self.baserow.create_row(cfg.baserow_table_productions, {
            "title": topic,
            "status": "em_producao",
        })
        production_id = prod_row["id"]
        logger.info(f"VideoCrew: production_id={production_id}")

        # Fase 1: Pesquisa + Style Guide
        cal_result = self.calendario.execute(topic)
        logger.info("VideoCrew: pesquisa concluída")

        # Fase 2: Roteiro
        rot_result = self.roteirista.execute(
            topic=topic,
            research=cal_result["research"],
            style_guide=cal_result["style_guide"],
        )
        logger.info("VideoCrew: roteiro gerado")

        # Fase 3: Revisão
        rev_result = self.revisor.execute(rot_result["script"])
        logger.info(f"VideoCrew: revisão → {rev_result['status']}")

        # Fase 4: Narração ElevenLabs → MinIO
        nar_result = self.narrador.execute(
            script=rot_result["script"],
            production_id=production_id,
        )
        logger.info(f"VideoCrew: narração gerada — {nar_result.get('char_count', 0)} chars")

        self.baserow.update_row(cfg.baserow_table_productions, production_id, {
            "roteiro": rot_result["script"],
            "status": "em_producao",
        })

        # Fase 5: Thumbnail fal.ai
        thumbnail_prompts = rot_result.get("thumbnail_prompts", [])
        thumb_result = self.diretor_arte.execute(
            task="thumbnail",
            context={
                "topic": topic,
                "thumbnail_prompt": thumbnail_prompts[0] if thumbnail_prompts else None,
            },
        )
        logger.info(f"VideoCrew: thumbnail gerado → {thumb_result.get('thumbnail_url')}")

        self.baserow.update_row(cfg.baserow_table_productions, production_id, {
            "thumbnail_url": thumb_result.get("thumbnail_url"),
        })

        # Fase 6: Normalização NCA → re-upload MinIO → URL para HeyGen
        audio_path_raw = nar_result.get("audio_path")
        audio_result = self.editor_audio.execute(
            audio_path=audio_path_raw,
            normalize=True,
        )
        normalized_path = Path(audio_result["audio_path"])
        logger.info(f"VideoCrew: áudio normalizado → {normalized_path}")

        norm_key = f"productions/{production_id}/{uuid.uuid4().hex[:8]}_{normalized_path.name}"
        self.minio.upload_file(normalized_path, cfg.minio_bucket_work, norm_key)
        audio_url_for_heygen = self.minio.generate_presigned_url(
            cfg.minio_bucket_work,
            norm_key,
            7 * 24 * 3600,
        )
        logger.info(f"VideoCrew: áudio normalizado em MinIO → {audio_url_for_heygen}")

        # Fase 7: HeyGen avatar → download MP4
        video_id = self.heygen.generate_video(audio_url=audio_url_for_heygen)
        logger.info(f"VideoCrew: HeyGen job submetido → video_id={video_id}")

        self.baserow.update_row(cfg.baserow_table_productions, production_id, {
            "heygen_video_id": video_id,
        })

        heygen_video_url = self.heygen.wait_for_completion(video_id)
        logger.info(f"VideoCrew: HeyGen concluído → {heygen_video_url}")

        local_video = Path(f"/tmp/cirlene_{production_id}.mp4")
        self.heygen.download_video(heygen_video_url, local_video)
        logger.info(f"VideoCrew: vídeo baixado → {local_video}")

        # Fase 8: Publicação MinIO + Baserow posts
        pub_result = self.publicador.execute(
            video_path=local_video,
            production_id=production_id,
            title=topic,
            description=rot_result["script"][:500],
            tags="saude,bemestar,cirlenienia",
        )
        logger.info(f"VideoCrew: publicado → {pub_result['video_url']}")

        # Limpa temporários
        try:
            local_video.unlink(missing_ok=True)
            normalized_path.unlink(missing_ok=True)
        except Exception:
            pass

        return {
            "topic": topic,
            "production_id": production_id,
            "research": cal_result["research"],
            "script": rot_result["script"],
            "validation": rev_result["status"],
            "thumbnail_url": thumb_result.get("thumbnail_url"),
            "audio_path": audio_path_raw,
            "audio_url": nar_result.get("audio_url"),
            "heygen_video_id": video_id,
            "video_url": pub_result["video_url"],
            "post_ids": pub_result["post_ids"],
            "status": "published_to_queue",
        }

    def publish(
        self,
        video_path: str,
        production_id: int,
        title: str,
        description: str,
        tags: str = "",
    ) -> dict:
        """Upload vídeo finalizado e enfileira para publicação nas plataformas."""
        logger.info(f"VideoCrew: enfileirando publicação production_id={production_id}")
        return self.publicador.execute(
            video_path=video_path,
            production_id=production_id,
            title=title,
            description=description,
            tags=tags,
        )


def get_crew() -> VideoCrew:
    """Factory for VideoCrew."""
    return VideoCrew()
