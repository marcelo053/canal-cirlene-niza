import pytest
from unittest.mock import MagicMock
from cirleneniza.agents.revisor import RevisorEspecialista


def test_revisor_role():
    mock_gemini = MagicMock()
    agent = RevisorEspecialista(gemini=mock_gemini)
    assert agent.name == "Revisor Especialista"
    assert hasattr(agent, "validate_script")
    assert hasattr(agent, "execute")
    assert "científico" in agent.role.lower() or "saúde" in agent.role.lower()