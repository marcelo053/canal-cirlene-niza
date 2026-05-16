import pytest
from cirleneniza.tools.kokoro import KokoroClient


def test_kokoro_client_initialization():
    client = KokoroClient(endpoint="http://test:8880")
    assert client.endpoint == "http://test:8880"


def test_kokoro_voices_available():
    client = KokoroClient()
    voices = client.list_voices()
    assert "pm_alta" in voices
    assert len(voices) >= 3


def test_synthesize_method_exists():
    client = KokoroClient()
    assert hasattr(client, "synthesize")
