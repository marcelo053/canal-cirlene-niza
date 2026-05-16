import pytest
from cirleneniza.tools.baserow import BaserowClient


def test_client_initialization():
    client = BaserowClient(base_url="http://test.com", token="fake-token")
    assert client.base_url == "http://test.com"
    assert client.token == "fake-token"


def test_get_productions_method_exists():
    client = BaserowClient(base_url="http://test.com", token="fake-token")
    assert hasattr(client, "get_productions")
    assert hasattr(client, "create_production")
    assert hasattr(client, "update_scene")
    assert hasattr(client, "get_style_guide")