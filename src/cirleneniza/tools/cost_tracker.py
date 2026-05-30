from loguru import logger

from cirleneniza.tools.baserow import BaserowClient


class CostTracker:
    """Non-blocking cost logger to Baserow costs_cirlene table.

    All methods swallow exceptions so billing failures never interrupt production.
    Prices are estimates based on typical plan tiers — update as needed.
    """

    ELEVENLABS_PER_1K_CHARS = 0.30   # Creator plan ~$0.30/1K chars
    HEYGEN_PER_VIDEO = 0.50           # ~0.5 credit per video generation
    FAL_IMAGE = 0.025                 # fal.ai Flux dev, per image
    FAL_VIDEO = {5: 0.50, 10: 1.00}  # Kling i2v, per clip by duration

    def __init__(self, baserow: BaserowClient, table_id: int) -> None:
        self._baserow = baserow
        self._table_id = table_id

    def log(
        self,
        production_id: int,
        service: str,
        cost_usd: float,
        tokens_used: int = 0,
        description: str = "",
    ) -> None:
        try:
            self._baserow.create_row(self._table_id, {
                "production_id": production_id,
                "service": service,
                "cost_usd": round(cost_usd, 4),
                "tokens_used": tokens_used,
                "description": description,
            })
            logger.debug(f"CostTracker: {service} ${cost_usd:.4f} | production={production_id}")
        except Exception as e:
            logger.warning(f"CostTracker: falha ao registrar custo ({service}): {e}")

    def log_elevenlabs(self, production_id: int, char_count: int, description: str = "ElevenLabs TTS") -> None:
        cost = char_count / 1000 * self.ELEVENLABS_PER_1K_CHARS
        self.log(production_id, "elevenlabs", cost, description=f"{description} ({char_count} chars)")

    def log_heygen(self, production_id: int, n_videos: int = 1, description: str = "HeyGen avatar") -> None:
        cost = n_videos * self.HEYGEN_PER_VIDEO
        self.log(production_id, "heygen", cost, description=f"{description} ({n_videos} vídeo(s))")

    def log_fal_image(self, production_id: int, n_images: int = 1, description: str = "fal.ai Flux image") -> None:
        cost = n_images * self.FAL_IMAGE
        self.log(production_id, "fal", cost, description=f"{description} ({n_images} imagem(ns))")

    def log_fal_video(
        self,
        production_id: int,
        n_clips: int = 1,
        duration_s: int = 5,
        description: str = "fal.ai Kling video",
    ) -> None:
        unit = self.FAL_VIDEO.get(10 if duration_s > 5 else 5, 0.50)
        cost = n_clips * unit
        self.log(production_id, "fal", cost, description=f"{description} ({n_clips} clip(s) x {duration_s}s)")
