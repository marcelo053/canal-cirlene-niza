import re
from loguru import logger
from pathlib import Path
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
    """Agente Narrador — TTS narração via Kokoro."""

    def __init__(
        self,
        kokoro: KokoroClient | None = None,
        minio: MinIOClient | None = None,
    ):
        self.kokoro = kokoro or KokoroClient()
        self.minio = minio or MinIOClient()
        self.name = "Narrador"
        self.role = (
            "Narrador profissional de vídeos de saúde e bem-estar. "
            "Converte roteiros em narração TTS com a voz da Cirlene Niza."
        )
        self.goal = "Gerar narração TTS clara, emotiva e pronta para edição."

    def generate_narration(
        self,
        script: str,
        voice: str = "pm_alta",
        output_dir: Path | str | None = None,
    ) -> dict:
        """Converte script em áudio TTS."""
        clean_text = strip_stage_directions(script)

        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / "narration.wav"
            audio_path = self.kokoro.synthesize(clean_text, voice, output_path)
        else:
            audio_path = self.kokoro.synthesize(clean_text, voice)

        return {
            "audio_path": str(audio_path),
            "voice": voice,
            "char_count": len(clean_text),
            "duration_estimate_sec": len(clean_text) // 15,
        }

    def execute(
        self,
        script: str,
        voice: str = "pm_alta",
        production_id: int | None = None,
    ) -> dict:
        """Executa geração de narração completa."""
        logger.info("Narrador: gerando narração TTS")
        result = self.generate_narration(script, voice)

        if production_id:
            audio_key = f"productions/{production_id}/narration.wav"
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
