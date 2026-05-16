import pytest
from cirleneniza.agents.editor_video import EditorVideo


def test_editor_video_initialization():
    agente = EditorVideo()
    assert agente.name == "Editor de Vídeo"
    assert hasattr(agente, "compose_video")
    assert hasattr(agente, "apply_ken_burns")
    assert hasattr(agente, "generate_srt")
