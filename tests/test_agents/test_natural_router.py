import sys
import json
from unittest.mock import MagicMock, patch

# Mock anthropic before importing MiniMaxClient
sys.modules.setdefault("anthropic", MagicMock())

from cirleneniza.bot.natural_router import NaturalLanguageRouter


def _valid_response(intent, params=None, reply="ok"):
    return json.dumps({"intent": intent, "params": params or {}, "reply": reply})


def test_initialization():
    with patch("cirleneniza.bot.natural_router.MiniMaxClient"):
        router = NaturalLanguageRouter()
        assert hasattr(router, "route")


def test_route_parses_novo_tema_intent():
    with patch("cirleneniza.bot.natural_router.MiniMaxClient") as MockLLM:
        MockLLM().generate.return_value = _valid_response("novo_tema", {"topic": "proteína"})
        router = NaturalLanguageRouter()
        result = router.route("quero falar sobre proteína", {})
    assert result["intent"] == "novo_tema"
    assert result["params"]["topic"] == "proteína"
    assert result["reply"] == "ok"


def test_route_parses_produzir_intent():
    with patch("cirleneniza.bot.natural_router.MiniMaxClient") as MockLLM:
        MockLLM().generate.return_value = _valid_response("produzir")
        router = NaturalLanguageRouter()
        result = router.route("produz o vídeo", {})
    assert result["intent"] == "produzir"


def test_route_strips_markdown_fences():
    raw_json = json.dumps({"intent": "status", "params": {}, "reply": "veja o status"})
    with patch("cirleneniza.bot.natural_router.MiniMaxClient") as MockLLM:
        MockLLM().generate.return_value = f"```json\n{raw_json}\n```"
        router = NaturalLanguageRouter()
        result = router.route("qual o status?", {})
    assert result["intent"] == "status"


def test_route_returns_fallback_on_invalid_json():
    with patch("cirleneniza.bot.natural_router.MiniMaxClient") as MockLLM:
        MockLLM().generate.return_value = "isso não é json válido"
        router = NaturalLanguageRouter()
        result = router.route("algo", {})
    assert result["intent"] == "conversa"
    assert "reply" in result


def test_route_returns_fallback_on_exception():
    with patch("cirleneniza.bot.natural_router.MiniMaxClient") as MockLLM:
        MockLLM().generate.side_effect = Exception("LLM indisponível")
        router = NaturalLanguageRouter()
        result = router.route("algo", {})
    assert result["intent"] == "conversa"


def test_route_includes_session_context_in_call():
    with patch("cirleneniza.bot.natural_router.MiniMaxClient") as MockLLM:
        MockLLM().generate.return_value = _valid_response("conversa")
        router = NaturalLanguageRouter()
        session = {"topic": "vitamina D", "step": "roteiro_ok"}
        router.route("e agora?", session)
        call_prompt = MockLLM().generate.call_args[1]["prompt"]
        assert "vitamina D" in call_prompt
        assert "roteiro_ok" in call_prompt


def test_route_corrigir_intent_with_params():
    with patch("cirleneniza.bot.natural_router.MiniMaxClient") as MockLLM:
        MockLLM().generate.return_value = _valid_response("corrigir", {"instrucao": "intro muito longa"})
        router = NaturalLanguageRouter()
        result = router.route("a intro ficou longa demais", {})
    assert result["intent"] == "corrigir"
    assert result["params"]["instrucao"] == "intro muito longa"
