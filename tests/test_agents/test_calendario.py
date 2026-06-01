import json
import pytest
from unittest.mock import MagicMock
from cirleneniza.agents.calendario import CalendarioEditorial


def _make_agent(research_response=None, style_response=None):
    mock_llm = MagicMock()
    mock_llm.generate.side_effect = [
        research_response or json.dumps({
            "points": ["Proteína preserva massa muscular", "Reduz apetite em 30%"],
            "key_data": ["73% dos estudos confirmam"]
        }),
        style_response or json.dumps({
            "palette": ["#E07B39", "#F5F0E8", "#2D5A27", "#FFFFFF"],
            "visual_tone": "quente e acolhedor",
            "visual_reference": "fotografia de alimentos naturais",
            "composition": "regra dos terços com foco no alimento"
        }),
    ]
    return CalendarioEditorial(llm=mock_llm)


def test_calendario_has_required_methods():
    agent = _make_agent()
    assert agent.name == "Calendário Editorial"
    assert hasattr(agent, "research_topic")
    assert hasattr(agent, "generate_style_guide")
    assert hasattr(agent, "execute")


def test_research_topic_returns_structured_data():
    agent = _make_agent()
    result = agent.research_topic("proteína")
    assert "research_data" in result
    assert "points" in result["research_data"]
    assert len(result["research_data"]["points"]) >= 1


def test_generate_style_guide_returns_structured_data():
    agent = _make_agent()
    research = agent.research_topic("proteína")
    style = agent.generate_style_guide("proteína", research["research"])
    assert "style_guide_data" in style
    assert "palette" in style["style_guide_data"]


def test_execute_returns_backward_compat_strings():
    """research e style_guide ainda devem ser strings para compatibilidade."""
    agent = _make_agent()
    result = agent.execute("proteína")
    assert isinstance(result["research"], str)
    assert isinstance(result["style_guide"], str)
    assert len(result["research"]) > 0


def test_execute_also_returns_structured_dicts():
    agent = _make_agent()
    result = agent.execute("proteína")
    assert "research_data" in result
    assert "style_guide_data" in result
    assert isinstance(result["research_data"]["points"], list)
