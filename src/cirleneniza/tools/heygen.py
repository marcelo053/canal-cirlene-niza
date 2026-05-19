import time
import requests
from pathlib import Path
from loguru import logger


class HeyGenClient:
    """HeyGen API client — avatar video generation via talking photo."""

    BASE_URL = "https://api.heygen.com"

    def __init__(self, api_key: str, talking_photo_id: str):
        self.talking_photo_id = talking_photo_id
        self.session = requests.Session()
        self.session.headers.update({"X-Api-Key": api_key})

    def generate_video(self, audio_url: str) -> str:
        """Submit video generation job. Returns video_id."""
        payload = {
            "video_inputs": [
                {
                    "character": {
                        "type": "talking_photo",
                        "talking_photo_id": self.talking_photo_id,
                    },
                    "voice": {
                        "type": "audio",
                        "audio_url": audio_url,
                    },
                }
            ],
            "dimension": {"width": 1080, "height": 1920},
        }
        resp = self.session.post(f"{self.BASE_URL}/v2/video/generate", json=payload)
        resp.raise_for_status()
        video_id = resp.json()["data"]["video_id"]
        logger.info(f"HeyGen: job submitted → video_id={video_id}")
        return video_id

    def wait_for_completion(
        self,
        video_id: str,
        timeout: int = 600,
        poll_interval: int = 15,
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
