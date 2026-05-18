import pytest
from unittest.mock import patch
from cirleneniza.agents.narrador import Narrador, strip_stage_directions


def test_strip_stage_directions():
    text = "Olá [pausa] pessoal! (sorrindo) Vamos *aprender* juntos."
    result = strip_stage_directions(text)
    assert "[" not in result
    assert "(" not in result
    assert "*" not in result
    assert "Olá" in result


def test_narrador_initialization():
    from unittest.mock import MagicMock
    from cirleneniza.tools.elevenlabs import ElevenLabsClient
    mock_el = MagicMock(spec=ElevenLabsClient)
    mock_el.voice_id = "test-voice-id"
    with patch("boto3.client"):
        agente = Narrador(elevenlabs=mock_el)
        assert agente.name == "Narrador"
        assert hasattr(agente, "generate_narration")
        assert hasattr(agente, "execute")
