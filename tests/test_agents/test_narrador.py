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


def test_elevenlabs_settings_for_narration():
    """Verifica stability=0.62, similarity_boost=0.75, style=0.0."""
    from unittest.mock import MagicMock
    from cirleneniza.tools.elevenlabs import ElevenLabsClient
    mock_el = MagicMock(spec=ElevenLabsClient)
    mock_el.voice_id = "test_voice"
    mock_el.synthesize.return_value = "/tmp/test.mp3"
    mock_minio = MagicMock()

    agent = Narrador(elevenlabs=mock_el, minio=mock_minio)
    agent.generate_narration("Texto de teste para narração.", output_dir=None)

    call_kwargs = mock_el.synthesize.call_args[1]
    assert call_kwargs.get("stability") == 0.62
    assert call_kwargs.get("similarity_boost") == 0.75
    assert call_kwargs.get("style") == 0.0


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
