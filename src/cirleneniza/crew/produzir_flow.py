# src/cirleneniza/crew/produzir_flow.py
"""ProduzirFlow — Pipeline Canal Cirlene Niza como CrewAI Flow com estado Pydantic."""
from crewai.flow.flow import Flow, listen, start
from loguru import logger
from pydantic import BaseModel

from cirleneniza.agents.calendario import CalendarioEditorial
from cirleneniza.agents.diretor_arte import DiretorDeArte
from cirleneniza.agents.editor_audio import EditorAudio
from cirleneniza.agents.editor_video import EditorVideo
from cirleneniza.agents.gerador_cenas import GeradorCenas
from cirleneniza.agents.gerador_prompts import GeradorDePrompts
from cirleneniza.agents.gerador_slides import GeradorSlidesCientificos
from cirleneniza.agents.narrador import Narrador
from cirleneniza.agents.publicador import Publicador
from cirleneniza.agents.revisor import RevisorEspecialista
from cirleneniza.agents.roteirista import RoteiristaCirleneNiza
from cirleneniza.config import get_settings
from cirleneniza.models.production import (
    AudioOutput,
    ResearchOutput,
    ScriptOutput,
    StyleGuideOutput,
    ValidationOutput,
)
from cirleneniza.tools.baserow import BaserowClient
from cirleneniza.tools.cost_tracker import CostTracker
from cirleneniza.tools.heygen import HeyGenClient
from cirleneniza.tools.minio import MinIOClient
from cirleneniza.tools.nca_toolkit import NCAToolkitClient


def _extract_locutor_lines(main_section: str) -> str:
    """Extrai apenas linhas LOCUTOR do MAIN para TTS."""
    lines = []
    for line in main_section.split("\n"):
        stripped = line.strip()
        if stripped.startswith("LOCUTOR:"):
            text = stripped.replace("LOCUTOR:", "").strip()
            if text:
                lines.append(text)
    return " ".join(lines)


class ProductionState(BaseModel):
    topic: str = ""
    production_id: int | None = None
    research: ResearchOutput | None = None
    style_guide: StyleGuideOutput | None = None
    script: ScriptOutput | None = None
    script_raw: dict = {}
    validation: ValidationOutput | None = None
    audios: AudioOutput | None = None
    scene_images: list[dict] = []
    scene_videos: list[dict] = []
    slide_urls: list[str] = []
    thumbnail_url: str = ""
    heygen_video_id: str = ""
    final_video_url: str = ""
    post_ids: dict[str, int] = {}
    status: str = "pending"


class ProduzirFlow(Flow[ProductionState]):
    """Pipeline de produção como CrewAI Flow com estado Pydantic."""

    def __init__(self):
        super().__init__()
        cfg = get_settings()
        self.calendario = CalendarioEditorial()
        self.roteirista = RoteiristaCirleneNiza()
        self.revisor = RevisorEspecialista()
        self.narrador = Narrador()
        self.editor_audio = EditorAudio()
        self.gerador_prompts = GeradorDePrompts()
        self.gerador_cenas = GeradorCenas()
        self.diretor_arte = DiretorDeArte()
        self.minio = MinIOClient(
            endpoint=cfg.minio_endpoint.removeprefix("http://"),
            access_key=cfg.minio_access_key,
            secret_key=cfg.minio_secret_key,
            bucket_work=cfg.minio_bucket_work,
            bucket_final=cfg.minio_bucket_final,
            public_endpoint=cfg.minio_public_endpoint or None,
        )
        self.gerador_slides = GeradorSlidesCientificos(minio=self.minio)
        self.editor_video = EditorVideo(
            nca=NCAToolkitClient(cfg.nca_toolkit_url, api_key=cfg.nca_api_key)
        )
        self.publicador = Publicador()
        self.heygen = HeyGenClient(
            api_key=cfg.heygen_api_key,
            talking_photo_id=cfg.heygen_talking_photo_id,
        )
        self.baserow = BaserowClient(
            base_url=cfg.baserow_url,
            token=cfg.baserow_token,
        )
        self.tracker = CostTracker(self.baserow, cfg.baserow_table_costs)
        self._cfg = cfg

    @start()
    def pesquisar(self):
        logger.info(f"ProduzirFlow: pesquisando '{self.state.topic}'")
        result = self.calendario.execute(self.state.topic)
        self.state.research = ResearchOutput(
            topic=result["topic"],
            points=result.get("research_data", {}).get("points", [result["research"]]),
            key_data=result.get("research_data", {}).get("key_data", []),
        )
        self.state.style_guide = StyleGuideOutput(
            palette=result.get("style_guide_data", {}).get("palette", ["#E07B39"]),
            visual_tone=result.get("style_guide_data", {}).get("visual_tone", ""),
            visual_reference=result.get("style_guide_data", {}).get("visual_reference", ""),
            composition=result.get("style_guide_data", {}).get("composition", ""),
        )

    @listen(pesquisar)
    def escrever_roteiro(self):
        logger.info("ProduzirFlow: escrevendo roteiro")
        result = self.roteirista.execute(
            topic=self.state.topic,
            research=self.state.research.model_dump_json() if self.state.research else "",
            style_guide="\n".join(self.state.style_guide.palette) if self.state.style_guide else "",
        )
        self.state.script_raw = result
        self.state.script = ScriptOutput(
            intro=result["intro"],
            main=result["main"],
            outro=result["outro"],
            full_script=result["full_script"],
            cena_prompts=result["cena_prompts"],
            thumbnail_prompts=result.get("thumbnail_prompts", []),
        )

    @listen(escrever_roteiro)
    def revisar(self):
        logger.info("ProduzirFlow: revisando roteiro")
        result = self.revisor.execute(self.state.script.full_script)
        self.state.validation = ValidationOutput(
            claims=result["claims"],
            overall_score=result["overall_score"],
        )
        logger.info(f"ProduzirFlow: revisão → {self.state.validation.status}")

    @listen(revisar)
    def produzir(self):
        """Fases de produção: narração, cenas, slides, thumbnail, montagem, publicação."""
        cfg = self._cfg
        sd = self.state.script
        topic = self.state.topic
        production_id = self.state.production_id

        if not production_id:
            prod_row = self.baserow.create_row(cfg.baserow_table_productions, {
                "title": topic,
                "status": "em_producao",
            })
            self.state.production_id = prod_row["id"]
            production_id = self.state.production_id

        logger.info("ProduzirFlow: gerando narrações")
        main_narration = _extract_locutor_lines(sd.main)
        audio_intro = self.narrador.execute(sd.intro, production_id)
        audio_main = self.narrador.execute(main_narration, production_id)
        audio_outro = self.narrador.execute(sd.outro, production_id)

        norm_intro = self.editor_audio.execute(audio_intro["audio_path"], normalize=True)
        norm_main = self.editor_audio.execute(audio_main["audio_path"], normalize=True)
        norm_outro = self.editor_audio.execute(audio_outro["audio_path"], normalize=True)

        self.state.audios = AudioOutput(
            intro_path=audio_intro["audio_path"],
            main_path=audio_main["audio_path"],
            outro_path=audio_outro["audio_path"],
            normalized_paths={
                "intro": norm_intro["audio_path"],
                "main": norm_main["audio_path"],
                "outro": norm_outro["audio_path"],
            },
        )
        total_chars = len(sd.intro) + len(main_narration) + len(sd.outro)
        self.tracker.log_elevenlabs(production_id, total_chars, "intro+main+outro")

        logger.info("ProduzirFlow: enriquecendo prompts e gerando cenas")
        enriched_cenas = self.gerador_prompts.execute(
            [c.model_dump() for c in sd.cena_prompts]
        )
        scene_result = self.gerador_cenas.execute(
            cena_prompts=enriched_cenas,
            main_audio_duration=audio_main.get("duration_estimate_sec", 120),
        )
        self.state.scene_images = scene_result.get("scene_images", [])
        self.state.scene_videos = scene_result.get("scene_videos", [])

        slide_result = self.gerador_slides.execute(
            research=self.state.script_raw.get("main", ""),
            topic=topic,
            production_id=production_id,
        )
        self.state.slide_urls = slide_result.get("slide_urls", [])

        thumbnail_prompts = sd.thumbnail_prompts
        thumb_result = self.diretor_arte.execute(
            task="thumbnail",
            context={
                "topic": topic,
                "thumbnail_prompt": thumbnail_prompts[0] if thumbnail_prompts else None,
            },
        )
        self.state.thumbnail_url = thumb_result.get("thumbnail_url", "")
        self.baserow.update_row(cfg.baserow_table_productions, production_id, {
            "thumbnail_url": self.state.thumbnail_url,
        })
        self.tracker.log_fal_image(production_id, 1, "thumbnail Flux")

        video_segments = [v["video_url"] for v in self.state.scene_videos if v.get("video_url")]
        if video_segments:
            final_video = self.editor_video.compose_from_segments(
                video_paths=video_segments,
                main_audio=norm_main["audio_path"],
            )
            pub_result = self.publicador.execute(
                video_path=final_video,
                production_id=production_id,
                title=topic,
                description=sd.full_script[:500],
                tags="saude,bemestar,cirleneniza",
            )
            self.state.final_video_url = pub_result.get("video_url", "")
            self.state.post_ids = pub_result.get("post_ids", {})

        self.state.status = "published_to_queue"
        logger.info(f"ProduzirFlow: produção concluída → {self.state.final_video_url}")
