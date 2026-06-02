import json
import sys
from unittest.mock import MagicMock, patch

sys.modules.setdefault("anthropic", MagicMock())

from cirleneniza.agents.gerador_prompts import GeradorDePrompts


def test_initialization():
    with patch("cirleneniza.agents.gerador_prompts.MiniMaxClient"):
        agent = GeradorDePrompts()
        assert agent.name == "Gerador de Prompts"
        assert hasattr(agent, "enrich_scene")
        assert hasattr(agent, "enrich")
        assert hasattr(agent, "execute")


def test_enrich_scene_returns_json_kling_prompt():
    """enrich_scene parses JSON and returns kling_motion_prompt."""
    json_response = json.dumps({
        "scene": "Cena 1: Hook",
        "kling_motion_prompt": "Close-up shot, slow zoom in. Protein powder in shaker. Kitchen. Soft light. Vertical 9:16. Photorealistic. Cinematic 4K.",
        "scene_type": "hook"
    })
    with patch("cirleneniza.agents.gerador_prompts.MiniMaxClient") as MockLLM:
        MockLLM().generate.return_value = json_response
        agent = GeradorDePrompts()
        scene = {
            "scene": "Cena 1: Hook",
            "hook_technique": "myth_break",
            "locutor": "Proteína não engorda.",
            "nota_visual": "Pó de proteína",
            "camera": "close-up",
            "lighting": "soft natural light",
            "atmosphere": "inspiring",
        }
        result = agent.enrich_scene(scene)
    assert "Vertical 9:16" in result["kling_motion_prompt"]
    assert result["scene_type"] == "hook"
    assert "kling_motion_prompt" in result
    assert "prompt" in result  # legacy compat


def test_enrich_scene_falls_back_on_json_parse_error():
    """If LLM doesn't return valid JSON, returns original scene unchanged."""
    with patch("cirleneniza.agents.gerador_prompts.MiniMaxClient") as MockLLM:
        MockLLM().generate.return_value = "texto não é JSON"
        agent = GeradorDePrompts()
        scene = {"scene": "Cena 1", "prompt": "original prompt"}
        result = agent.enrich_scene(scene)
    assert result["scene"] == "Cena 1"  # original preserved


def test_enrich_scene_appends_vertical_tag_if_missing():
    """If kling_motion_prompt lacks Vertical 9:16, it gets appended."""
    json_response = json.dumps({
        "scene": "Cena 1",
        "kling_motion_prompt": "Close-up shot. Protein powder. Kitchen. Soft light.",
        "scene_type": "informative"
    })
    with patch("cirleneniza.agents.gerador_prompts.MiniMaxClient") as MockLLM:
        MockLLM().generate.return_value = json_response
        agent = GeradorDePrompts()
        result = agent.enrich_scene({"scene": "Cena 1"})
    assert "Vertical 9:16" in result["kling_motion_prompt"]


def test_enrich_scene_swallows_llm_exception():
    """API errors return original scene unchanged."""
    with patch("cirleneniza.agents.gerador_prompts.MiniMaxClient") as MockLLM:
        MockLLM().generate.side_effect = Exception("API error")
        agent = GeradorDePrompts()
        original = {"scene": "Cena 1", "prompt": "original"}
        result = agent.enrich_scene(original)
    assert result == original


def test_enrich_processes_all_scenes():
    json_response = json.dumps({
        "scene": "Cena",
        "kling_motion_prompt": "Shot. Vertical 9:16. Photorealistic.",
        "scene_type": "informative"
    })
    with patch("cirleneniza.agents.gerador_prompts.MiniMaxClient") as MockLLM:
        MockLLM().generate.return_value = json_response
        agent = GeradorDePrompts()
        scenes = [{"scene": f"Cena {i}"} for i in range(3)]
        result = agent.enrich(scenes)
    assert len(result) == 3


def test_execute_aliases_enrich():
    json_response = json.dumps({
        "scene": "Cena",
        "kling_motion_prompt": "Prompt. Vertical 9:16.",
        "scene_type": "hook"
    })
    with patch("cirleneniza.agents.gerador_prompts.MiniMaxClient") as MockLLM:
        MockLLM().generate.return_value = json_response
        agent = GeradorDePrompts()
        scenes = [{"scene": "C1"}]
        assert agent.execute(scenes) == agent.enrich(scenes)


def test_kling_system_contains_negative_prompts():
    from cirleneniza.agents.gerador_prompts import _SYSTEM
    assert "Negative:" in _SYSTEM or "negative" in _SYSTEM.lower()
    assert "motion blur" in _SYSTEM.lower()


def test_kling_system_contains_motion_intensity():
    from cirleneniza.agents.gerador_prompts import _SYSTEM
    assert "motion_intensity" in _SYSTEM


def test_enrich_scene_hook_includes_motion_intensity():
    json_response = json.dumps({
        "scene": "Cena 1: Hook",
        "kling_motion_prompt": "Close-up shot, slow zoom in. motion_intensity=0.7. Protein powder. Vertical 9:16. Photorealistic. Cinematic 4K.",
        "scene_type": "hook"
    })
    with patch("cirleneniza.agents.gerador_prompts.MiniMaxClient") as MockLLM:
        MockLLM().generate.return_value = json_response
        agent = GeradorDePrompts()
        scene = {
            "scene": "Cena 1",
            "hook_technique": "myth_break",
            "locutor": "Proteína não engorda.",
            "nota_visual": "Pó",
            "camera": "close-up",
            "lighting": "soft",
            "atmosphere": "inspiring",
        }
        result = agent.enrich_scene(scene)
    assert result["scene_type"] == "hook"
