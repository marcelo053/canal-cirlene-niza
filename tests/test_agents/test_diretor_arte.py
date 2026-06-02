import sys
from unittest.mock import MagicMock

# Mock fal and crewai so we don't need actual packages installed
mock_fal = MagicMock()
mock_fal.settings = MagicMock()
mock_fal.subscribe = MagicMock(return_value={"images": [{"url": "https://example.com/logo.png"}]})
sys.modules["fal"] = mock_fal
sys.modules.setdefault("crewai", MagicMock())

import pytest
from cirleneniza.agents.diretor_arte import DiretorDeArte, load_prompt


def test_diretor_arte_identity():
    mock_client = MagicMock()
    agent = DiretorDeArte(fal_client=mock_client)
    assert agent.name == "Diretor de Arte"
    assert hasattr(agent, "generate_logo")
    assert hasattr(agent, "generate_thumbnail")
    assert hasattr(agent, "execute")


def test_load_prompt():
    prompt = load_prompt("logo_cn_terracota")
    assert "CN" in prompt or "logo" in prompt.lower()


def test_generate_logo():
    mock_client = MagicMock()
    mock_client.generate.return_value = {"images": [{"url": "https://example.com/logo.png"}]}
    agent = DiretorDeArte(fal_client=mock_client)
    result = agent.generate_logo("logo_cn_terracota")
    assert "logo_url" in result
    assert result["variant"] == "logo_cn_terracota"
    mock_client.generate.assert_called_once()


def test_generate_thumbnail():
    mock_client = MagicMock()
    mock_client.generate.return_value = {"images": [{"url": "https://example.com/thumb.png"}]}
    agent = DiretorDeArte(fal_client=mock_client)
    result = agent.generate_thumbnail("Vitaminas para imunidade")
    assert "thumbnail_url" in result
    assert result["topic"] == "Vitaminas para imunidade"
    mock_client.generate.assert_called_once()


def test_thumbnail_uses_flux_dev():
    """Thumbnail deve usar fal-ai/flux/dev, não /schnell."""
    mock_client = MagicMock()
    mock_client.generate.return_value = {"images": [{"url": "https://example.com/thumb.png"}]}
    agent = DiretorDeArte(fal_client=mock_client)
    agent.generate_thumbnail("proteína", "Protein powder in shaker")
    call_args = str(mock_client.generate.call_args)
    assert "flux/dev" in call_args
    assert "schnell" not in call_args


def test_thumbnail_prompt_includes_hex_color():
    """Prompt de thumbnail deve incluir o HEX #E07B39 da brand."""
    mock_client = MagicMock()
    mock_client.generate.return_value = {"images": [{"url": "https://example.com/thumb.png"}]}
    agent = DiretorDeArte(fal_client=mock_client)
    agent.generate_thumbnail("proteína", "Protein powder in shaker")
    prompt_used = mock_client.generate.call_args[0][0]
    assert "#E07B39" in prompt_used


def test_execute_unknown_task():
    mock_client = MagicMock()
    agent = DiretorDeArte(fal_client=mock_client)
    result = agent.execute("unknown_task")
    assert "error" in result