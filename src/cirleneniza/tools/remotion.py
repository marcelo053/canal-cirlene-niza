"""Remotion renderer — renders scientific slide compositions to MP4."""
import json
import subprocess
import time
from pathlib import Path

from loguru import logger

from cirleneniza.tools.minio import MinIOClient

_REMOTION_PROJECT = Path(__file__).resolve().parents[3] / "slides-cientificos"
_NPX = Path.home() / ".nvm/versions/node/v24.14.0/bin/npx"
_OUTPUT_DIR = Path("/tmp/remotion-slides")

# Maps composition ID → expected duration in frames (at 30fps)
COMPOSITION_FRAMES: dict[str, int] = {
    "StatCard": 120,
    "ComparisonBar": 150,
    "StudyQuote": 120,
    "BenefitsList": 160,
    "TimelineProgress": 150,
    "CircleStat": 150,
    "ScientificDefinition": 150,
}


class RemotionRenderer:
    """Renders Remotion scientific slide compositions and uploads to MinIO."""

    def __init__(self, minio: MinIOClient | None = None):
        self.minio = minio

    # ------------------------------------------------------------------
    # Core render
    # ------------------------------------------------------------------

    def render(
        self,
        composition_id: str,
        props: dict,
        output_filename: str | None = None,
    ) -> Path:
        """Render a composition to MP4. Returns local output path."""
        if composition_id not in COMPOSITION_FRAMES:
            raise ValueError(
                f"Unknown composition '{composition_id}'. "
                f"Valid: {list(COMPOSITION_FRAMES)}"
            )

        _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        if output_filename is None:
            ts = int(time.time())
            output_filename = f"{composition_id}_{ts}.mp4"

        output_path = _OUTPUT_DIR / output_filename

        cmd = [
            str(_NPX),
            "remotion", "render",
            "src/index.ts",
            composition_id,
            str(output_path),
            f"--props={json.dumps(props)}",
            "--log", "error",
        ]

        logger.info(f"RemotionRenderer: rendering '{composition_id}'")
        result = subprocess.run(
            cmd,
            cwd=str(_REMOTION_PROJECT),
            capture_output=True,
            text=True,
            timeout=300,
        )

        if result.returncode != 0:
            logger.error(f"Remotion stderr: {result.stderr[:800]}")
            raise RuntimeError(f"Remotion render failed for '{composition_id}': {result.stderr[:400]}")

        logger.info(f"RemotionRenderer: '{composition_id}' → {output_path}")
        return output_path

    def render_and_upload(
        self,
        composition_id: str,
        props: dict,
        minio_key: str | None = None,
    ) -> str:
        """Render and upload to MinIO. Returns presigned URL (or local path if no MinIO)."""
        path = self.render(composition_id, props)

        if self.minio is None:
            return str(path)

        if minio_key is None:
            minio_key = f"slides/{path.name}"

        self.minio.upload_file(path, self.minio.bucket_work, minio_key)
        url = self.minio.generate_presigned_url(self.minio.bucket_work, minio_key)
        path.unlink(missing_ok=True)

        logger.info(f"RemotionRenderer: uploaded → {url}")
        return url

    # ------------------------------------------------------------------
    # Batch render — renders multiple slides sequentially
    # ------------------------------------------------------------------

    def render_batch(
        self,
        slides: list[dict],
        production_id: int | None = None,
    ) -> list[dict]:
        """Render a list of slide specs. Each spec: {composition, props, key?}.

        Returns list of {composition, url, local_path?, error?}.
        """
        results = []
        for i, slide in enumerate(slides):
            composition = slide["composition"]
            props = slide["props"]
            key = slide.get("key") or (
                f"slides/prod{production_id}/{composition}_{i}.mp4"
                if production_id else None
            )
            try:
                url = self.render_and_upload(composition, props, key)
                results.append({"composition": composition, "url": url, "index": i})
            except Exception as e:
                logger.error(f"RemotionRenderer: slide {i} '{composition}' failed: {e}")
                results.append({"composition": composition, "url": None, "error": str(e), "index": i})

        return results
