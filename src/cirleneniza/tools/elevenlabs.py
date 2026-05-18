import requests
from pathlib import Path
from loguru import logger


class ElevenLabsClient:
    """ElevenLabs TTS client — voz clonada da Cirlene Niza."""

    BASE_URL = "https://api.elevenlabs.io/v1"

    def __init__(self, api_key: str, voice_id: str):
        self.api_key = api_key
        self.voice_id = voice_id
        self.session = requests.Session()
        self.session.headers.update({"xi-api-key": api_key})

    def synthesize(
        self,
        text: str,
        output_path: Path | str | None = None,
        model_id: str = "eleven_multilingual_v2",
        stability: float = 0.5,
        similarity_boost: float = 0.75,
    ) -> Path:
        """Converte texto em áudio MP3 com voz clonada."""
        url = f"{self.BASE_URL}/text-to-speech/{self.voice_id}"
        payload = {
            "text": text,
            "model_id": model_id,
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity_boost,
            },
        }
        resp = self.session.post(url, json=payload, headers={"Accept": "audio/mpeg"})
        resp.raise_for_status()

        if output_path is None:
            output_path = Path("/tmp/narration.mp3")
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(resp.content)

        logger.info(f"ElevenLabs: áudio gerado → {output_path} ({len(resp.content):,} bytes)")
        return output_path
