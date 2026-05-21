import time
import requests
from pathlib import Path
from loguru import logger


class HeyGenClient:
    """HeyGen API client — avatar video generation via talking photo."""

    BASE_URL = "https://api.heygen.com"

    def __init__(self, api_key: str, talking_photo_id: str):
        self.talking_photo_id = talking_photo_id
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({"X-Api-Key": api_key})

    def upload_audio(self, audio_path: Path | str) -> str:
        """Upload audio to HeyGen to generate word-timing metadata. Returns asset_id."""
        audio_path = Path(audio_path)
        with open(audio_path, "rb") as f:
            resp = requests.post(
                f"{self.BASE_URL}/v3/assets",
                headers={"X-Api-Key": self.api_key},
                files={"file": (audio_path.name, f)},
                timeout=120,
            )
        resp.raise_for_status()
        asset_id = resp.json()["data"]["asset_id"]
        logger.info(f"HeyGen: audio uploaded → asset_id={asset_id}")
        return asset_id

    def generate_video(self, audio_asset_id: str | None = None, audio_url: str | None = None) -> str:
        """Submit video generation job. Returns video_id."""
        if audio_asset_id:
            voice = {"type": "audio", "audio_asset_id": audio_asset_id}
        elif audio_url:
            voice = {"type": "audio", "audio_url": audio_url}
        else:
            raise ValueError("Must provide either audio_asset_id or audio_url")

        payload = {
            "video_inputs": [
                {
                    "character": {
                        "type": "talking_photo",
                        "talking_photo_id": self.talking_photo_id,
                    },
                    "voice": voice,
                }
            ],
            "dimension": {"width": 1920, "height": 1080},
        }
        resp = self.session.post(f"{self.BASE_URL}/v2/video/generate", json=payload)
        resp.raise_for_status()
        video_id = resp.json()["data"]["video_id"]
        logger.info(f"HeyGen: job submitted → video_id={video_id}")
        return video_id

    def wait_for_completion(
        self,
        video_id: str,
        timeout: int = 1800,
        poll_interval: int = 30,
    ) -> str:
        """Poll until video is ready. Returns video URL."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            resp = self.session.get(
                f"{self.BASE_URL}/v1/video_status.get",
                params={"video_id": video_id},
            )
            resp.raise_for_status()
            data = resp.json()["data"]
            status = data.get("status")
            logger.info(f"HeyGen: video_id={video_id} status={status}")
            if status == "completed":
                return data["video_url"]
            if status == "failed":
                raise RuntimeError(f"HeyGen video failed: {data.get('error')}")
            time.sleep(poll_interval)
        raise TimeoutError(f"HeyGen video_id={video_id} timed out after {timeout}s")

    def download_video(self, video_url: str, output_path: Path | str) -> Path:
        """Download completed video from HeyGen CDN."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        resp = requests.get(video_url, stream=True, timeout=120)
        resp.raise_for_status()
        with open(output_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        logger.info(f"HeyGen: downloaded → {output_path} ({output_path.stat().st_size:,} bytes)")
        return output_path
