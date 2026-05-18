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
    """Remove stage directions from script text before TTS."""
    result = text
    for pattern in STAGE_DIRECTION_PATTERNS:
        result = re.sub(pattern, "", result)
    result = re.sub(r"\s+", " ", result).strip()
    return result


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
        self.minio = minio or MinIOClient()
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
        clean_text = strip_stage_directions(script)

        output_path = None
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / "narration.mp3"

        audio_path = self.elevenlabs.synthesize(clean_text, output_path)

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
