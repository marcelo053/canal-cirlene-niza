import pytest
from unittest.mock import patch

from cirleneniza.agents.roteirista import RoteiristaCirleneNiza


@patch("cirleneniza.agents.roteirista.GeminiClient")
def test_roteirista_persona(mock_gemini):
    agent = RoteiristaCirleneNiza()
    assert agent.name == "Roteirista"
    assert "empática" in agent.backstory.lower() or "coach" in agent.backstory.lower()
    assert hasattr(agent, "generate_script")
    assert hasattr(agent, "generate_thumbnail_prompts")