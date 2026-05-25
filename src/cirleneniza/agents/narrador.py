import re
from loguru import logger
from pathlib import Path
from cirleneniza.config import get_settings
from cirleneniza.tools.elevenlabs import ElevenLabsClient
from cirleneniza.tools.kokoro import KokoroClient
from cirleneniza.tools.minio import MinIOClient


STAGE_DIRECTION_PATTERNS = [
    r"\[.*?\]",
    r"\(.*?\)",
    r"\*.*?\*",
]


def strip_stage_directions(text: str) -> str:
    """Remove stage directions, preserve ellipses and natural pause markers."""
    result = text
    for pattern in STAGE_DIRECTION_PATTERNS:
        result = re.sub(pattern, "", result)
    result = re.sub(r"\s+", " ", result).strip()
    return result


def prepare_for_tts(text: str) -> str:
    """Prepare script text for ElevenLabs — strip directions, enhance pause markers.

    ElevenLabs eleven_multilingual_v2 treats '...' as a natural pause.
    Commas and sentence breaks also create breathing room.
    We normalize spacing without collapsing intentional '...' pauses.
    """
    text = strip_stage_directions(text)
    # Normalize multiple dots to exactly three (pause marker)
    text = re.sub(r"\.{4,}", "...", text)
    # Ensure space after ellipsis if missing
    text = re.sub(r"\.\.\.([A-Za-záéíóúâêîôûãõàèìòùçÁÉÍÓÚÂÊÎÔÛÃÕÀÈÌÒÙÇ])", r"... \1", text)
    return text.strip()


class Narrador:
    """Agente Narrador — TTS via ElevenLabs (voz clonada Cirlene) com fallback Kokoro."""

    def __init__(
        self,
        elevenlabs: ElevenLabsClient | None = None,
        kokoro: KokoroClient | None = None,
        minio: MinIOClient | None = None,
    ):
        if elevenlabs is None:
            cfg = get_settings()
            elevenlabs = ElevenLabsClient(
                api_key=cfg.elevenlabs_api_key,
                voice_id=cfg.elevenlabs_voice_id,
            )
        self.elevenlabs = elevenlabs
        self.kokoro = kokoro or KokoroClient()
        if minio is None:
            cfg = get_settings()
            minio = MinIOClient(
                endpoint=cfg.minio_endpoint.removeprefix("http://"),
                access_key=cfg.minio_access_key,
                secret_key=cfg.minio_secret_key,
                bucket_work=cfg.minio_bucket_work,
                bucket_final=cfg.minio_bucket_final,
                public_endpoint=cfg.minio_public_endpoint or None,
            )
        self.minio = minio
        self.name = "Narrador"
        self.role = (
            "Narrador profissional de vídeos de saúde e bem-estar. "
            "Converte roteiros em narração TTS com a voz clonada da Cirlene Niza."
        )
        self.goal = "Gerar narração TTS clara, emotiva e pronta para edição."

    def generate_narration(
        self,
        script: str,
        output_dir: Path | str | None = None,
    ) -> dict:
        """Converte script em áudio MP3 via ElevenLabs voz clonada."""
        clean_text = prepare_for_tts(script)

        output_path = None
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / "narration.mp3"

        # stability=0.35 → mais expressiva, variação natural de entonação
        # similarity_boost=0.80 → mantém identidade da voz clonada
        # style=0.45 → exagera estilo da voz original (ElevenLabs v2 param)
        audio_path = self.elevenlabs.synthesize(
            clean_text,
            output_path,
            stability=0.35,
            similarity_boost=0.80,
            style=0.45,
        )

        return {
            "audio_path": str(audio_path),
            "voice_id": self.elevenlabs.voice_id,
            "char_count": len(clean_text),
            "duration_estimate_sec": len(clean_text) // 15,
        }

    def execute(
        self,
        script: str,
        production_id: int | None = None,
    ) -> dict:
        """Executa geração de narração completa."""
        logger.info("Narrador: gerando narração via ElevenLabs")
        result = self.generate_narration(script)

        if production_id:
            audio_key = f"productions/{production_id}/narration.mp3"
            self.minio.upload_file(
                Path(result["audio_path"]),
                self.minio.bucket_work,
                audio_key,
            )
            result["audio_url"] = self.minio.generate_presigned_url(
                self.minio.bucket_work,
                audio_key,
            )

        return result
