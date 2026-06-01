import pytest
from unittest.mock import patch

from cirleneniza.agents.roteirista import RoteiristaCirleneNiza


@patch("cirleneniza.agents.roteirista.MiniMaxClient")
def test_roteirista_persona(mock_minimax):
    agent = RoteiristaCirleneNiza()
    assert agent.name == "Roteirista"
    assert "empática" in agent.backstory.lower() or "coach" in agent.backstory.lower()
    assert hasattr(agent, "generate_script")
    assert hasattr(agent, "generate_thumbnail_prompts")


def test_roteirista_execute_returns_full_script_key():
    """Garante que execute() retorna 'full_script', não 'script'."""
    from unittest.mock import MagicMock, patch
    with patch("cirleneniza.agents.roteirista.MiniMaxClient") as MockLLM:
        MockLLM.return_value.generate.return_value = _minimal_script_raw()
        agent = RoteiristaCirleneNiza()
        result = agent.execute(
            topic="proteína",
            research="pesquisa",
            style_guide="guia",
        )
    assert "full_script" in result, "'full_script' deve estar no resultado de execute()"


def _minimal_script_raw() -> str:
    return """## INTRO
Oi pessoal, hoje vamos falar sobre proteína.

## MAIN
##Cena 1: O mito##
HOOK: myth_break
LOCUTOR: Todo mundo diz que proteína engorda. A ciência prova o contrário.
CAMERA: close-up + slow-zoom-in
KLING PROMPT: Close-up shot, slow zoom in. Protein powder in shaker. Kitchen. Soft light. Vertical 9:16. Photorealistic.
NOTA VISUAL: Pó de proteína
LIGHTING: soft natural light
ATMOSPHERE: inspiring

##Cena 2: Absorção##
HOOK:
LOCUTOR: Em 30 minutos o whey chega ao músculo. Rápido assim.
CAMERA: medium-shot + slow-pan-right
KLING PROMPT: Medium shot, slow pan right. Stopwatch ticking. Glowing particles. Dark background. Warm light. Vertical 9:16. Photorealistic.
NOTA VISUAL: Cronômetro
LIGHTING: studio warm
ATMOSPHERE: energetic

##Cena 3: Dado##
HOOK:
LOCUTOR: 73% dos estudos confirmam. Proteína não engorda. Ela constrói.
CAMERA: close-up + slow-zoom-in
KLING PROMPT: Close-up shot, slow zoom in. Scientific chart glowing on screen. Lab environment. Blue light. Vertical 9:16. Photorealistic.
NOTA VISUAL: Gráfico científico
LIGHTING: studio warm
ATMOSPHERE: energetic

##Cena 4: CTA##
HOOK:
LOCUTOR: Salva esse vídeo porque você vai querer mostrar pra quem ainda acredita no mito.
CAMERA: wide-shot + slow-zoom-in
KLING PROMPT: Wide shot, slow zoom in. Meal prep containers on counter. Colorful vegetables. Woman's hands. Warm afternoon light. Vertical 9:16. Photorealistic.
NOTA VISUAL: Marmitas organizadas
LIGHTING: golden hour
ATMOSPHERE: warm

##Cena 5: Reflexão##
HOOK:
LOCUTOR: Você já sabia disso? Me conta nos comentários o que mudou na sua alimentação.
CAMERA: medium-shot + handheld
KLING PROMPT: Medium shot, handheld. Brazilian woman 40s curly hair smiling at camera. Clean kitchen. Natural light. Warm tones. Vertical 9:16. Photorealistic.
NOTA VISUAL: Cirlene olhando para câmera
LIGHTING: soft natural light
ATMOSPHERE: warm

##Cena 6: Conclusão##
HOOK:
LOCUTOR: Com consistência e informação certa. Seu corpo responde. Sempre.
CAMERA: close-up + slow-zoom-in
KLING PROMPT: Close-up shot, slow zoom in. Healthy meal colorful plate on table. Fresh ingredients. Natural light streaming through window. Warm inviting tones. Vertical 9:16. Photorealistic.
NOTA VISUAL: Prato saudável
LIGHTING: golden hour
ATMOSPHERE: inspiring

## OUTRO
Obrigada por assistir! Me segue para mais conteúdos de saúde com base científica."""


import json as _json

_PLAN_RESPONSE = _json.dumps({
    "hook_type": "myth_break",
    "hook_rationale": "A maioria acredita que proteína engorda — derruba o mito imediatamente",
    "narrative_arc": ["mito da proteína", "absorção rápida", "dado 73%", "CTA orgânico",
                      "pergunta reflexiva", "conclusão motivadora"],
    "cta_position": 4,
    "reflection_position": 5,
    "key_data_to_use": ["73% dos estudos", "30 minutos para absorção"]
})


def test_roteirista_has_plan_script_method():
    with patch("cirleneniza.agents.roteirista.MiniMaxClient"):
        agent = RoteiristaCirleneNiza()
    assert hasattr(agent, "_plan_script")


def test_plan_script_returns_dict_with_hook_type():
    with patch("cirleneniza.agents.roteirista.MiniMaxClient") as MockLLM:
        MockLLM.return_value.generate.return_value = _PLAN_RESPONSE
        agent = RoteiristaCirleneNiza()
        plan = agent._plan_script("proteína", "pesquisa científica")
    assert plan["hook_type"] in ("myth_break", "immediate_benefit",
                                  "counter_intuitive", "mirror_question")
    assert "narrative_arc" in plan
    assert len(plan["narrative_arc"]) >= 6


def test_plan_script_fallback_on_json_error():
    """Se o LLM não retornar JSON, deve retornar plano padrão sem crash."""
    with patch("cirleneniza.agents.roteirista.MiniMaxClient") as MockLLM:
        MockLLM.return_value.generate.return_value = "resposta não é JSON"
        agent = RoteiristaCirleneNiza()
        plan = agent._plan_script("proteína", "pesquisa")
    assert "hook_type" in plan