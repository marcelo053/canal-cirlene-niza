import json
import pytest
from unittest.mock import MagicMock
from cirleneniza.agents.revisor import RevisorEspecialista


def _make_agent(response=None):
    mock_llm = MagicMock()
    mock_llm.generate.return_value = response or json.dumps({
        "claims": [
            {"claim": "Proteína não engorda", "status": "ok", "suggestion": None},
            {"claim": "Emagrece 10kg em 1 semana", "status": "errado",
             "suggestion": "Perda de peso saudável é 0.5-1kg/semana"}
        ],
        "overall_score": 0.5
    })
    return RevisorEspecialista(llm=mock_llm)


def test_revisor_has_required_attributes():
    agent = _make_agent()
    assert agent.name == "Revisor Especialista"
    assert hasattr(agent, "validate_script")
    assert hasattr(agent, "execute")


def test_validate_script_returns_claims_list():
    agent = _make_agent()
    result = agent.validate_script("roteiro de teste")
    assert "claims" in result
    assert isinstance(result["claims"], list)
    assert len(result["claims"]) >= 1


def test_execute_status_needs_revision_when_errado():
    agent = _make_agent()
    result = agent.execute("roteiro com claim errado")
    assert result["status"] == "needs_revision"


def test_execute_status_approved_when_no_errado():
    mock_llm = MagicMock()
    mock_llm.generate.return_value = json.dumps({
        "claims": [
            {"claim": "Proteína preserva músculo", "status": "ok", "suggestion": None},
        ],
        "overall_score": 1.0
    })
    agent = RevisorEspecialista(llm=mock_llm)
    result = agent.execute("roteiro ok")
    assert result["status"] == "approved"


def test_execute_preserves_original_script():
    agent = _make_agent()
    result = agent.execute("meu roteiro original")
    assert result["original_script"] == "meu roteiro original"
