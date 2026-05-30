import sys
from unittest.mock import MagicMock, patch

# Mock anthropic before importing MiniMaxClient
sys.modules.setdefault("anthropic", MagicMock())

from cirleneniza.agents.gerador_prompts import GeradorDePrompts


def test_initialization():
    with patch("cirleneniza.agents.gerador_prompts.MiniMaxClient"):
        agent = GeradorDePrompts()
        assert agent.name == "Gerador de Prompts"
        assert hasattr(agent, "enrich_scene")
        assert hasattr(agent, "enrich")
        assert hasattr(agent, "execute")


# --- _extract_prompt (static, no mocking needed) ---

def test_extract_prompt_with_markers():
    raw = "some reasoning\nKLING_PROMPT_START\nClose-up shot of Cirlene.\nKLING_PROMPT_END\nend"
    result = GeradorDePrompts._extract_prompt(raw)
    assert result == "Close-up shot of Cirlene."


def test_extract_prompt_fallback_camera_terms():
    raw = "Here is my analysis.\n\nClose-up shot with slow zoom in. Cirlene smiles. Kitchen background. Natural light."
    result = GeradorDePrompts._extract_prompt(raw)
    assert "close-up" in result.lower() or "zoom" in result.lower()


def test_extract_prompt_last_line_fallback():
    raw = "short text\nno camera terms here\nfinal line"
    result = GeradorDePrompts._extract_prompt(raw)
    assert result == "final line"


def test_extract_prompt_appends_vertical_tag_if_missing():
    with patch("cirleneniza.agents.gerador_prompts.MiniMaxClient") as MockLLM:
        MockLLM().generate.return_value = (
            "KLING_PROMPT_START\nClose-up shot. Cirlene smiles.\nKLING_PROMPT_END"
        )
        agent = GeradorDePrompts()
        scene = {"scene": "Cena 1", "prompt": "original"}
        result = agent.enrich_scene(scene)
        assert "Vertical 9:16" in result["kling_motion_prompt"]


def test_enrich_scene_calls_llm_and_returns_updated_scene():
    with patch("cirleneniza.agents.gerador_prompts.MiniMaxClient") as MockLLM:
        MockLLM().generate.return_value = (
            "KLING_PROMPT_START\n"
            "Close-up of Cirlene. Camera zooms in. Kitchen. Natural light. "
            "Vertical 9:16. Photorealistic. Cinematic 4K.\n"
            "KLING_PROMPT_END"
        )
        agent = GeradorDePrompts()
        scene = {"scene": "Cena 1", "prompt": "original", "camera": "close-up"}
        result = agent.enrich_scene(scene)
        assert "kling_motion_prompt" in result
        assert "prompt" in result
        assert "Cirlene" in result["kling_motion_prompt"]


def test_enrich_scene_swallows_llm_exception():
    with patch("cirleneniza.agents.gerador_prompts.MiniMaxClient") as MockLLM:
        MockLLM().generate.side_effect = Exception("API error")
        agent = GeradorDePrompts()
        original = {"scene": "Cena 1", "prompt": "original"}
        result = agent.enrich_scene(original)
        assert result == original  # returns unchanged scene


def test_enrich_processes_all_scenes():
    with patch("cirleneniza.agents.gerador_prompts.MiniMaxClient") as MockLLM:
        MockLLM().generate.return_value = (
            "KLING_PROMPT_START\nSome prompt. Vertical 9:16. Photorealistic.\nKLING_PROMPT_END"
        )
        agent = GeradorDePrompts()
        scenes = [{"scene": f"Cena {i}"} for i in range(3)]
        result = agent.enrich(scenes)
        assert len(result) == 3


def test_execute_aliases_enrich():
    with patch("cirleneniza.agents.gerador_prompts.MiniMaxClient") as MockLLM:
        MockLLM().generate.return_value = (
            "KLING_PROMPT_START\nPrompt. Vertical 9:16.\nKLING_PROMPT_END"
        )
        agent = GeradorDePrompts()
        scenes = [{"scene": "C1"}]
        assert agent.execute(scenes) == agent.enrich(scenes)
