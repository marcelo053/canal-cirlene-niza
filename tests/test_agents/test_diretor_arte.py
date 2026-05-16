import sys
from unittest.mock import MagicMock

# Mock the `fal` module so we don't need the actual package installed
mock_fal = MagicMock()
mock_fal.settings = MagicMock()
mock_fal.subscribe = MagicMock(return_value={"images": [{"url": "https://example.com/logo.png"}]})
sys.modules["fal"] = mock_fal

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


def test_execute_unknown_task():
    mock_client = MagicMock()
    agent = DiretorDeArte(fal_client=mock_client)
    result = agent.execute("unknown_task")
    assert "error" in result