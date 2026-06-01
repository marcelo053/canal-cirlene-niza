# tests/test_tools/test_minimax.py
import pytest
from unittest.mock import MagicMock, patch


def test_minimax_retries_on_cjk_output():
    """Se o primeiro output tem >5% CJK, deve tentar novamente."""
    cjk_response = "这是一个测试" * 20   # >5% CJK
    clean_response = "Este é o texto correto em português."

    with patch("cirleneniza.tools.minimax.MiniMaxClient._call_api") as mock_api:
        mock_api.side_effect = [cjk_response, clean_response]
        from cirleneniza.tools.minimax import MiniMaxClient
        client = MiniMaxClient.__new__(MiniMaxClient)
        client.api_key = "fake"
        result = client.generate("prompt", retries=2)

    assert result == clean_response
    assert mock_api.call_count == 2


def test_minimax_no_retry_on_clean_output():
    clean_response = "Texto limpo em português."

    with patch("cirleneniza.tools.minimax.MiniMaxClient._call_api") as mock_api:
        mock_api.return_value = clean_response
        from cirleneniza.tools.minimax import MiniMaxClient
        client = MiniMaxClient.__new__(MiniMaxClient)
        client.api_key = "fake"
        result = client.generate("prompt", retries=2)

    assert result == clean_response
    assert mock_api.call_count == 1
