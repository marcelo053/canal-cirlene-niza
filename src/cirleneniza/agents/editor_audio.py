import subprocess
from loguru import logger
from pathlib import Path
from cirleneniza.tools.nca_toolkit import NCAToolkitClient


class EditorAudio:
    """Agente Editor de Áudio — mixagem, limpeza, normalização."""

    def __init__(self, nca: NCAToolkitClient | None = None):
        self.nca = nca or NCAToolkitClient()
        self.name = "Editor de Áudio"
        self.role = (
            "Editor de áudio especializado em conteúdo de saúde. "
            "Mixa narração + música ambiente, normaliza loudness (-14 LUFS)."
        )
        self.goal = "Entregar áudio final com qualidade profissional e loudness padrão."

    def normalize(self, audio_path: Path | str, target_lufs: float = -14.0) -> Path:
        """Normalize audio to YouTube standard loudness."""
        return self.nca.normalize_audio(audio_path, target_lufs)

    def mix_with_music(
        self,
        narration: Path | str,
        music: Path | str,
        output: Path | str | None = None,
        narration_level: float = 0.8,
        music_level: float = 0.2,
    ) -> Path:
        """Mix narration with background music."""
        narration = Path(narration)
        music = Path(music)

        if output is None:
            output = narration.with_name(f"{narration.stem}_mixed.wav")
        output = Path(output)

        cmd = [
            "ffmpeg", "-y",
            "-i", str(narration),
            "-i", str(music),
            "-filter_complex",
            (
                f"[0:a]volume={narration_level}[nar];"
                f"[1:a]volume={music_level}[mus];"
                "[nar][mus]amix=inputs=2:duration=first[mixed]"
            ),
            "-map", "[mixed]",
            "-c:a", "pcm_s16le",
            str(output),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"Mix error: {result.stderr}")
            raise RuntimeError(f"Mix failed: {result.stderr}")

        logger.info(f"Audio mixed: {output}")
        return output

    def execute(
        self,
        audio_path: str,
        normalize: bool = True,
        mix_music: Path | str | None = None,
    ) -> dict:
        """Execute audio processing pipeline."""
        logger.info("Editor de Áudio: processando áudio")
        result_path = Path(audio_path)

        if normalize:
            result_path = self.normalize(result_path)

        if mix_music:
            result_path = self.mix_with_music(result_path, mix_music)

        return {
            "audio_path": str(result_path),
            "status": "processed",
        }
