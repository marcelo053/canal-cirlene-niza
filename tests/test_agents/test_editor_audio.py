import pytest
from cirleneniza.agents.editor_audio import EditorAudio


def test_editor_audio_initialization():
    agente = EditorAudio()
    assert agente.name == "Editor de Áudio"
    assert hasattr(agente, "normalize")
    assert hasattr(agente, "mix_with_music")
    assert hasattr(agente, "execute")
