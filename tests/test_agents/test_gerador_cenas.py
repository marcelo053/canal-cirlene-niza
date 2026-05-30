import sys
from unittest.mock import MagicMock

# Mock fal_client before importing the agent
sys.modules.setdefault("fal_client", MagicMock())

from cirleneniza.agents.gerador_cenas import GeradorCenas


def _make_agent():
    mock_fal = MagicMock()
    mock_fal.generate_image.return_value = {"url": "https://cdn.fal.ai/img.jpg"}
    mock_fal.generate_video.return_value = {"url": "https://cdn.fal.ai/vid.mp4", "duration": 5}
    return GeradorCenas(fal_client=mock_fal), mock_fal


def test_initialization():
    agent, _ = _make_agent()
    assert agent.name == "Gerador de Cenas"
    assert hasattr(agent, "execute")
    assert hasattr(agent, "generate_scene_images")
    assert hasattr(agent, "generate_scene_videos")


def test_execute_empty_prompts():
    agent, mock_fal = _make_agent()
    result = agent.execute(cena_prompts=[])
    assert result["scene_images"] == []
    assert result["scene_videos"] == []
    assert result["status"] == "generated"
    mock_fal.generate_image.assert_not_called()


def test_execute_returns_expected_keys():
    agent, _ = _make_agent()
    result = agent.execute(cena_prompts=[{"scene": "Cena 1", "kling_motion_prompt": "Close-up shot..."}])
    assert "scene_images" in result
    assert "scene_videos" in result
    assert len(result["scene_images"]) == 1
    assert len(result["scene_videos"]) == 1


def test_generate_scene_images_strips_kling_terms():
    agent, mock_fal = _make_agent()
    prompt_with_terms = "Close-up shot. Woman smiling. Vertical 9:16. Photorealistic. Kitchen."
    agent.generate_scene_images([{"scene": "Cena 1", "kling_motion_prompt": prompt_with_terms}])
    used_prompt = mock_fal.generate_image.call_args[1]["prompt"]
    assert "Vertical 9:16." not in used_prompt
    assert "Photorealistic." not in used_prompt
    assert "Kitchen" in used_prompt


def test_generate_scene_images_appends_style_context():
    agent, mock_fal = _make_agent()
    agent.generate_scene_images(
        [{"scene": "Cena 1", "kling_motion_prompt": "Close-up."}],
        style_context="warm tones",
    )
    used_prompt = mock_fal.generate_image.call_args[1]["prompt"]
    assert "warm tones" in used_prompt


def test_generate_scene_images_preserves_kling_prompt_for_video():
    agent, _ = _make_agent()
    original_kling = "Camera pans left. Cirlene gestures."
    images = agent.generate_scene_images([{"scene": "C1", "kling_motion_prompt": original_kling}])
    assert images[0]["kling_motion_prompt"] == original_kling


def test_generate_scene_images_uses_aspect_ratio_9_16():
    agent, mock_fal = _make_agent()
    agent.generate_scene_images([{"scene": "C1", "prompt": "some prompt"}])
    assert mock_fal.generate_image.call_args[1]["aspect_ratio"] == "9:16"


def test_generate_scene_videos_uses_kling_motion_prompt():
    agent, mock_fal = _make_agent()
    scene_images = [{
        "scene_index": 0,
        "scene_name": "C1",
        "image_url": "http://img.jpg",
        "kling_motion_prompt": "Slow zoom in. Cirlene smiles.",
        "prompt": "fallback prompt",
    }]
    agent.generate_scene_videos(scene_images, main_audio_duration=30)
    used_prompt = mock_fal.generate_video.call_args[1]["prompt"]
    assert used_prompt == "Slow zoom in. Cirlene smiles."


def test_apply_correction_appends_to_prompt():
    agent, mock_fal = _make_agent()
    current_data = {
        "cena_prompts": [{"kling_motion_prompt": "Original prompt.", "prompt": "Original prompt."}]
    }
    result = agent.apply_correction(scene_index=0, correction="make it brighter", current_data=current_data)
    assert "Original prompt." in result["prompt"]
    assert "make it brighter" in result["prompt"]
