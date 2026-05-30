import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, call

# Mock boto3 before any import that might pull it in
sys.modules.setdefault("boto3", MagicMock())

from cirleneniza.agents.publicador import Publicador, PLATFORMS


def _mock_settings():
    cfg = MagicMock()
    cfg.minio_bucket_final = "cirlene-final"
    cfg.minio_public_endpoint = "http://186.202.209.88:9000"
    cfg.minio_endpoint = "http://localhost:9000"
    cfg.baserow_table_productions = 726
    cfg.baserow_table_posts = 728
    return cfg


def _make_publicador():
    mock_minio = MagicMock()
    mock_baserow = MagicMock()
    mock_baserow.create_row.return_value = {"id": 99}
    with patch("cirleneniza.agents.publicador.get_settings", return_value=_mock_settings()):
        pub = Publicador(minio=mock_minio, baserow=mock_baserow)
    return pub, mock_minio, mock_baserow


def test_initialization():
    pub, _, _ = _make_publicador()
    assert hasattr(pub, "execute")
    assert hasattr(pub, "minio")
    assert hasattr(pub, "baserow")


def test_execute_uploads_video_to_minio():
    pub, mock_minio, _ = _make_publicador()
    with patch("cirleneniza.agents.publicador.get_settings", return_value=_mock_settings()):
        pub.execute(video_path="/tmp/video.mp4", production_id=1, title="Vitamina D", description="Desc")
    mock_minio.upload_file.assert_called_once()
    args = mock_minio.upload_file.call_args[0]
    assert args[1] == "cirlene-final"  # correct bucket


def test_execute_creates_post_for_each_platform():
    pub, _, mock_baserow = _make_publicador()
    with patch("cirleneniza.agents.publicador.get_settings", return_value=_mock_settings()):
        result = pub.execute(
            video_path="/tmp/video.mp4",
            production_id=1,
            title="Proteína",
            description="Desc",
        )
    assert mock_baserow.create_row.call_count == len(PLATFORMS)
    platforms_used = {c[0][1]["platform"] for c in mock_baserow.create_row.call_args_list}
    assert platforms_used == set(PLATFORMS)


def test_execute_sets_post_status_pronto():
    pub, _, mock_baserow = _make_publicador()
    with patch("cirleneniza.agents.publicador.get_settings", return_value=_mock_settings()):
        pub.execute("/tmp/v.mp4", 1, "T", "D")
    for c in mock_baserow.create_row.call_args_list:
        row = c[0][1]
        assert row["status"] == "pronto"


def test_execute_updates_production_status():
    pub, _, mock_baserow = _make_publicador()
    with patch("cirleneniza.agents.publicador.get_settings", return_value=_mock_settings()):
        pub.execute("/tmp/v.mp4", production_id=5, title="T", description="D")
    mock_baserow.update_row.assert_called_once()
    _, row_id, fields = mock_baserow.update_row.call_args[0]
    assert row_id == 5
    assert fields["status"] == "pronto"


def test_execute_returns_expected_keys():
    pub, _, _ = _make_publicador()
    with patch("cirleneniza.agents.publicador.get_settings", return_value=_mock_settings()):
        result = pub.execute("/tmp/v.mp4", 1, "T", "D")
    assert "video_url" in result
    assert "post_ids" in result
    assert "production_id" in result
    assert result["status"] == "published_to_queue"


def test_execute_custom_platforms():
    pub, _, mock_baserow = _make_publicador()
    with patch("cirleneniza.agents.publicador.get_settings", return_value=_mock_settings()):
        pub.execute("/tmp/v.mp4", 1, "T", "D", platforms=["youtube"])
    assert mock_baserow.create_row.call_count == 1
