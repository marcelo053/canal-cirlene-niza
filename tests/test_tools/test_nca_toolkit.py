import pytest
from cirleneniza.tools.nca_toolkit import NCAToolkitClient


def test_nca_client_initialization():
    client = NCAToolkitClient(url="http://test:8080")
    assert client.url == "http://test:8080"


def test_nca_methods_exist():
    client = NCAToolkitClient()
    assert hasattr(client, "generate_captions")
    assert hasattr(client, "normalize_audio")
