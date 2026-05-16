import pytest
from unittest.mock import MagicMock
from cirleneniza.agents.calendario import CalendarioEditorial


def test_calendario_returns_style_guide():
    mock_gemini = MagicMock()
    mock_gemini.generate.return_value = "research result"
    agent = CalendarioEditorial(gemini=mock_gemini)
    assert agent.name == "Calendário Editorial"
    assert hasattr(agent, "research_topic")
    assert hasattr(agent, "generate_style_guide")
    assert hasattr(agent, "execute")