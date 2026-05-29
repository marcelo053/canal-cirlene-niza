"""NCA Toolkit client — correct endpoints for stephengpope/no-code-architects-toolkit.

API requires:
  - POST /v1/media/transcribe
  - Header: X-API-Key
  - Body: JSON {"media_url": "<public url>", "include_srt": true, "language": "pt"}
  - Response: {"srt": "<srt content>", ...} or queued job
"""
import time
import requests
from loguru import logger
from pathlib import Path


class NCAToolkitClient:
    """NCA Toolkit client for transcription and subtitles."""

    def __init__(self, url: str = "http://localhost:8080", api_key: str = ""):
        self.url = url.rstrip("/")
        self.api_key = api_key
        self.session = requests.Session()
        if api_key:
            self.session.headers["X-API-Key"] = api_key

    def transcribe(
        self,
        media_url: str,
        language: str = "pt",
        include_srt: bool = True,
        words_per_line: int = 7,
        timeout: int = 300,
    ) -> dict:
        """Transcribe audio/video URL. Returns dict with 'text' and 'srt' keys."""
        payload = {
            "media_url": media_url,
            "language": language,
            "include_text": True,
            "include_srt": include_srt,
            "response_type": "direct",
            "words_per_line": words_per_line,
        }
        resp = self.session.post(
            f"{self.url}/v1/media/transcribe",
            json=payload,
            timeout=timeout,
        )
        resp.raise_for_status()
        data = resp.json()

        # Handle queued response (status != 200 in response body)
        if data.get("code") not in (200, None) or data.get("status") in ("processing", "queued"):
            job_id = data.get("job_id")
            if job_id:
                data = self._poll_job(job_id, timeout=timeout)

        # Unwrap nested response: {"response": {"srt": ..., "text": ...}}
        if "response" in data and isinstance(data["response"], dict):
            inner = data["response"]
            data = {**data, **inner}  # merge, inner wins

        logger.info(f"NCAToolkit: transcribed {media_url[:60]} → srt {len(data.get('srt') or '')}")
        return data

    def _poll_job(self, job_id: str, timeout: int = 300) -> dict:
        """Poll job status until complete."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            resp = self.session.get(f"{self.url}/v1/toolkit/status/{job_id}", timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "complete":
                    return data.get("result", data)
                if data.get("status") == "failed":
                    raise RuntimeError(f"NCA job {job_id} failed: {data}")
            time.sleep(5)
        raise TimeoutError(f"NCA job {job_id} timed out after {timeout}s")

    def generate_captions_srt(
        self,
        media_url: str,
        language: str = "pt",
        words_per_line: int = 7,
    ) -> str:
        """Return SRT string for media at public URL."""
        result = self.transcribe(media_url, language=language, words_per_line=words_per_line)
        return result.get("srt", "")

    def save_srt(
        self,
        media_url: str,
        output_path: Path | str,
        language: str = "pt",
    ) -> Path:
        """Transcribe and save SRT file. Returns path."""
        srt = self.generate_captions_srt(media_url, language=language)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(srt, encoding="utf-8")
        logger.info(f"NCAToolkit: SRT saved → {output_path} ({len(srt)} chars)")
        return output_path
