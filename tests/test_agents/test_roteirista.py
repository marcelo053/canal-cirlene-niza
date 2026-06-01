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