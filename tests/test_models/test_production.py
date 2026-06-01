import pytest
from pydantic import ValidationError
from cirleneniza.models.production import (
    CenaPrompt,
    ScriptOutput,
    ClaimResult,
    ValidationOutput,
    ResearchOutput,
    StyleGuideOutput,
    EnrichedScene,
)


def _make_cena(**kwargs):
    defaults = dict(
        scene="Cena 1: Título",
        hook_technique="myth_break",
        locutor="Todo mundo diz que proteína engorda a ciência prova o contrário.",
        camera="close-up + slow-zoom-in",
        kling_motion_prompt="Close-up shot, slow zoom in. Protein powder. Kitchen. Soft light. Vertical 9:16.",
        nota_visual="Pó de proteína caindo",
        lighting="soft natural light",
        atmosphere="inspiring",
    )
    defaults.update(kwargs)
    return CenaPrompt(**defaults)


def test_cena_prompt_valid():
    cena = _make_cena()
    assert cena.scene == "Cena 1: Título"


def test_cena_prompt_locutor_max_35_words():
    with pytest.raises(ValidationError, match="35 palavras"):
        _make_cena(locutor=" ".join(["palavra"] * 36))


def test_cena_prompt_kling_must_contain_9x16():
    with pytest.raises(ValidationError, match="9:16"):
        _make_cena(kling_motion_prompt="Close-up shot. Kitchen. Soft light.")


def test_cena_prompt_kling_min_80_chars():
    short = "Close-up shot. Vertical 9:16."  # < 80 chars
    with pytest.raises(ValidationError, match="80"):
        _make_cena(kling_motion_prompt=short)


def test_script_output_min_six_scenes():
    cenas = [_make_cena(scene=f"Cena {i}") for i in range(5)]  # only 5
    with pytest.raises(ValidationError, match="6 cenas"):
        ScriptOutput(
            intro="intro text",
            main="main text",
            outro="outro text",
            full_script="full",
            cena_prompts=cenas,
            thumbnail_prompts=[],
        )


def test_script_output_valid_with_six_scenes():
    cenas = [_make_cena(scene=f"Cena {i}") for i in range(6)]
    script = ScriptOutput(
        intro="intro text",
        main="main text",
        outro="outro text",
        full_script="full",
        cena_prompts=cenas,
        thumbnail_prompts=["prompt1"],
    )
    assert len(script.cena_prompts) == 6


def test_validation_output_derives_needs_revision_on_errado():
    claims = [
        ClaimResult(claim="claim1", status="ok"),
        ClaimResult(claim="claim2", status="errado", suggestion="corrigir"),
    ]
    result = ValidationOutput(claims=claims, overall_score=0.5)
    assert result.status == "needs_revision"


def test_validation_output_approved_when_no_errado():
    claims = [
        ClaimResult(claim="claim1", status="ok"),
        ClaimResult(claim="claim2", status="vago", suggestion="adicionar dado"),
    ]
    result = ValidationOutput(claims=claims, overall_score=0.9)
    assert result.status == "approved"


def test_research_output_valid():
    r = ResearchOutput(
        topic="proteína",
        points=["ponto 1", "ponto 2"],
        key_data=["73% dos atletas"],
    )
    assert r.topic == "proteína"


def test_style_guide_output_valid():
    sg = StyleGuideOutput(
        palette=["#E07B39", "#F5F0E8"],
        visual_tone="quente e acolhedor",
        visual_reference="fotografia de alimentos",
        composition="regra dos terços",
    )
    assert sg.palette[0] == "#E07B39"


def test_enriched_scene_valid():
    es = EnrichedScene(
        scene="Cena 1: Hook",
        kling_motion_prompt="Close-up shot, slow zoom in. Protein powder. Vertical 9:16.",
        scene_type="hook",
        prompt="Close-up shot, slow zoom in. Protein powder. Vertical 9:16.",
    )
    assert es.scene_type == "hook"
