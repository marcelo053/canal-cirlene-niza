import uuid
from pathlib import Path
from loguru import logger

from cirleneniza.config import get_settings
from cirleneniza.tools.baserow import BaserowClient
from cirleneniza.tools.minio import MinIOClient

PLATFORMS = ["youtube", "tiktok", "instagram"]
PRESIGNED_TTL = 7 * 24 * 3600  # 7 dias — suficiente para n8n processar


class Publicador:
    """Faz upload do vídeo final para MinIO e cria posts pendentes no Baserow."""

    def __init__(
        self,
        minio: MinIOClient | None = None,
        baserow: BaserowClient | None = None,
    ):
        cfg = get_settings()
        self.minio = minio or MinIOClient(
            endpoint=cfg.minio_endpoint.removeprefix("http://"),
            access_key=cfg.minio_access_key,
            secret_key=cfg.minio_secret_key,
            bucket_work=cfg.minio_bucket_work,
            bucket_final=cfg.minio_bucket_final,
        )
        self.baserow = baserow or BaserowClient(
            base_url=cfg.baserow_url,
            token=cfg.baserow_token,
        )
        self._cfg = cfg

    def execute(
        self,
        video_path: str | Path,
        production_id: int,
        title: str,
        description: str,
        tags: str = "",
        platforms: list[str] | None = None,
    ) -> dict:
        """
        1. Upload vídeo para MinIO cirlene-final
        2. Gera URL pré-assinada (7 dias)
        3. Cria post row para cada plataforma com status=pronto
        4. Atualiza productions row com video_final_url + status=pronto

        Returns dict com video_url e post_ids por plataforma.
        """
        cfg = self._cfg
        video_path = Path(video_path)
        platforms = platforms or PLATFORMS

        # --- Upload MinIO ---
        key = f"productions/{production_id}/{uuid.uuid4().hex[:8]}_{video_path.name}"
        self.minio.upload_file(video_path, cfg.minio_bucket_final, key)
        video_url = self.minio.generate_presigned_url(cfg.minio_bucket_final, key, PRESIGNED_TTL)
        logger.info(f"Publicador: upload OK → {video_url}")

        # --- Criar posts no Baserow ---
        post_ids: dict[str, int] = {}
        for platform in platforms:
            row = self.baserow.create_row(cfg.baserow_table_posts, {
                "production_id": production_id,
                "platform":      platform,
                "status":        "pronto",
                "video_url":     video_url,
                "title":         title,
                "description":   description,
                "tags":          tags,
            })
            post_ids[platform] = row["id"]
            logger.info(f"Publicador: post criado [{platform}] id={row['id']}")

        # --- Atualizar produção ---
        self.baserow.update_row(cfg.baserow_table_productions, production_id, {
            "video_final_url": video_url,
            "status":          "pronto",
        })
        logger.info(f"Publicador: production {production_id} → status=pronto")

        return {
            "production_id": production_id,
            "video_url":     video_url,
            "post_ids":      post_ids,
            "status":        "published_to_queue",
        }
