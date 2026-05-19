from cirleneniza.agents.calendario import CalendarioEditorial
from cirleneniza.agents.roteirista import RoteiristaCirleneNiza
from cirleneniza.agents.revisor import RevisorEspecialista
from cirleneniza.agents.narrador import Narrador
from cirleneniza.agents.editor_video import EditorVideo
from cirleneniza.agents.editor_audio import EditorAudio
from cirleneniza.agents.publicador import Publicador
from loguru import logger


class VideoCrew:
    """Pipeline Canal Cirlene Niza — execução direta via execute() de cada agente."""

    def __init__(self):
        self.calendario = CalendarioEditorial()
        self.roteirista = RoteiristaCirleneNiza()
        self.revisor = RevisorEspecialista()
        self.narrador = Narrador()
        self.editor_video = EditorVideo()
        self.editor_audio = EditorAudio()
        self.publicador = Publicador()

    def run(self, topic: str) -> dict:
        """Executa pipeline: pesquisa → roteiro → revisão."""
        logger.info(f"VideoCrew: iniciando pipeline para '{topic}'")

        # Fase 1: Pesquisa + Style Guide
        cal_result = self.calendario.execute(topic)
        logger.info("VideoCrew: pesquisa concluída")

        # Fase 2: Roteiro
        rot_result = self.roteirista.execute(
            topic=topic,
            research=cal_result["research"],
            style_guide=cal_result["style_guide"],
        )
        logger.info("VideoCrew: roteiro gerado")

        # Fase 3: Revisão
        rev_result = self.revisor.execute(rot_result["script"])
        logger.info(f"VideoCrew: revisão → {rev_result['status']}")

        return {
            "topic": topic,
            "research": cal_result["research"],
            "script": rot_result["script"],
            "validation": rev_result["status"],
            "thumbnail_prompts": rot_result.get("thumbnail_prompts", []),
            "status": "completed",
        }

    def publish(
        self,
        video_path: str,
        production_id: int,
        title: str,
        description: str,
        tags: str = "",
    ) -> dict:
        """Upload vídeo finalizado e enfileira para publicação nas plataformas."""
        logger.info(f"VideoCrew: enfileirando publicação production_id={production_id}")
        return self.publicador.execute(
            video_path=video_path,
            production_id=production_id,
            title=title,
            description=description,
            tags=tags,
        )


def get_crew() -> Crew:
    """Factory for VideoCrew."""
    return VideoCrew().build()