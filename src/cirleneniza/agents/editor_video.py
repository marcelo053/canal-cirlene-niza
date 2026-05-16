import subprocess
from loguru import logger
from pathlib import Path
from cirleneniza.tools.nca_toolkit import NCAToolkitClient


def run_ffmpeg(cmd: list[str]) -> None:
    """Execute FFmpeg command."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f"FFmpeg error: {result.stderr}")
        raise RuntimeError(f"FFmpeg failed: {result.stderr}")
    logger.info(f"FFmpeg completed: {' '.join(cmd[:3])}...")


class EditorVideo:
    """Agente Editor de Vídeo — montagem, captions, Ken Burns."""

    def __init__(self, nca: NCAToolkitClient | None = None):
        self.nca = nca or NCAToolkitClient()
        self.name = "Editor de Vídeo"
        self.role = (
            "Editor de vídeo especializado em conteúdo de saúde. "
            "Compõe vídeo com FFmpeg: backgrounds + narração + legendas."
        )
        self.goal = "Montar vídeo final com qualidade profissional."

    def generate_srt(self, audio_path: Path | str) -> Path:
        """Generate SRT subtitles from narration audio."""
        return self.nca.generate_captions(audio_path, language="pt")

    def compose_video(
        self,
        images: list[Path | str],
        audio: Path | str,
        srt: Path | str | None = None,
        output: Path | str | None = None,
    ) -> Path:
        """Compose video from images, audio, and optional subtitles."""
        images = [Path(p) for p in images]
        audio = Path(audio)
        if output is None:
            output = Path("/tmp/output_video.mp4")

        output = Path(output)
        output.parent.mkdir(parents=True, exist_ok=True)

        concat_list = output.parent / "concat_list.txt"
        with open(concat_list, "w") as f:
            for img in images:
                f.write(f"file '{img.resolve()}'\n")
                f.write("duration 5\n")
            f.write(f"file '{images[-1].resolve()}'\n")

        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(concat_list),
            "-i", str(audio),
        ]

        if srt:
            cmd.extend(["-vf", f"subtitles={Path(srt).name}"])

        cmd.extend([
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            "-c:a", "aac",
            "-shortest",
            str(output),
        ])

        run_ffmpeg(cmd)
        concat_list.unlink(missing_ok=True)

        logger.info(f"Video composed: {output}")
        return output

    def apply_ken_burns(self, image: Path | str, output: Path | str | None = None) -> Path:
        """Apply Ken Burns zoom effect to a single image."""
        image = Path(image)
        if output is None:
            output = image.with_name(f"{image.stem}_kb.mp4")

        output = Path(output)

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(image),
            "-vf", "zoompan=z='min(zoom+0.001,1.5)':d=125:s=1280x720",
            "-t", "5",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            str(output),
        ]

        run_ffmpeg(cmd)
        logger.info(f"Ken Burns applied: {output}")
        return output

    def execute(
        self,
        image_paths: list[str],
        audio_path: str,
        production_id: int | None = None,
    ) -> dict:
        """Execute video composition."""
        logger.info("Editor de Vídeo: compondo vídeo")

        video_path = self.compose_video(
            images=[Path(p) for p in image_paths],
            audio=audio_path,
        )

        return {
            "video_path": str(video_path),
            "status": "composed",
        }
