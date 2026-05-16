import requests
from loguru import logger
from pathlib import Path


class NCAToolkitClient:
    """NCA Toolkit client for subtitles and audio processing."""

    def __init__(self, url: str = "http://186.202.209.88:8080"):
        self.url = url.rstrip("/")

    def generate_captions(
        self,
        audio_path: Path | str,
        language: str = "pt",
    ) -> Path:
        """Generate SRT subtitles from audio via NCA Toolkit."""
        audio_path = Path(audio_path)

        with open(audio_path, "rb") as f:
            files = {"audio": (audio_path.name, f, "audio/wav")}
            data = {"language": language}

            response = requests.post(
                f"{self.url}/captions/generate",
                files=files,
                data=data,
                timeout=120,
            )
        response.raise_for_status()

        srt_path = audio_path.with_suffix(".srt")
        with open(srt_path, "w") as f:
            f.write(response.text)

        logger.info(f"Captions generated: {srt_path}")
        return srt_path

    def normalize_audio(
        self,
        audio_path: Path | str,
        target_lufs: float = -14.0,
    ) -> Path:
        """Normalize audio to target loudness (YouTube standard)."""
        audio_path = Path(audio_path)
        output_path = audio_path.with_name(f"{audio_path.stem}_normalized.wav")

        with open(audio_path, "rb") as f:
            files = {"audio": (audio_path.name, f, "audio/wav")}
            data = {"target_lufs": str(target_lufs)}

            response = requests.post(
                f"{self.url}/audio/normalize",
                files=files,
                data=data,
                timeout=60,
            )
        response.raise_for_status()

        with open(output_path, "wb") as f:
            f.write(response.content)

        logger.info(f"Audio normalized: {output_path}")
        return output_path
