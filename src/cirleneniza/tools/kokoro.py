import requests
from loguru import logger
from pathlib import Path


class KokoroClient:
    """Kokoro TTS client for Canal Cirlene Niza narration."""

    VOICES = {
        "pm_alta": "Alta — voz principal pt-BR feminina",
        "pm_santa": "Santa — voz pt-BR feminina calorosa",
        "pf_dora": "Dora — voz pt-BR feminina animada",
        "pm_liam": "Liam — voz pt-BR masculina",
    }

    def __init__(self, endpoint: str = "http://186.202.209.88:8880"):
        self.endpoint = endpoint.rstrip("/")

    def synthesize(
        self,
        text: str,
        voice: str = "pm_alta",
        output_path: Path | str | None = None,
    ) -> Path:
        """Generate TTS audio from text."""
        if output_path is None:
            output_path = Path(f"/tmp/kokoro_{hash(text)}.wav")

        payload = {
            "text": text,
            "voice": voice,
        }

        response = requests.post(
            f"{self.endpoint}/tts",
            json=payload,
            timeout=60,
        )
        response.raise_for_status()

        with open(output_path, "wb") as f:
            f.write(response.content)

        logger.info(f"TTS generated: {output_path}")
        return Path(output_path)

    def list_voices(self) -> dict[str, str]:
        """List available voices."""
        return self.VOICES.copy()
