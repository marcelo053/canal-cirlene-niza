import pytest
from unittest.mock import MagicMock, call
from cirleneniza.tools.cost_tracker import CostTracker


def _make_tracker():
    mock_baserow = MagicMock()
    mock_baserow.create_row.return_value = {"id": 1}
    return CostTracker(mock_baserow, table_id=730), mock_baserow


def test_log_calls_baserow_create_row():
    tracker, mock_br = _make_tracker()
    tracker.log(production_id=1, service="elevenlabs", cost_usd=0.09, description="test")
    mock_br.create_row.assert_called_once()
    _, row = mock_br.create_row.call_args[0]
    assert row["service"] == "elevenlabs"
    assert row["production_id"] == 1
    assert row["cost_usd"] == 0.09
    assert row["description"] == "test"


def test_log_rounds_cost_to_4_decimals():
    tracker, mock_br = _make_tracker()
    tracker.log(1, "fal", 0.123456789)
    _, row = mock_br.create_row.call_args[0]
    assert row["cost_usd"] == 0.1235


def test_log_swallows_exceptions():
    tracker, mock_br = _make_tracker()
    mock_br.create_row.side_effect = Exception("network error")
    tracker.log(1, "heygen", 0.50)  # must not raise


def test_log_elevenlabs_calculates_cost():
    tracker, mock_br = _make_tracker()
    tracker.log_elevenlabs(production_id=1, char_count=1000)
    _, row = mock_br.create_row.call_args[0]
    assert row["service"] == "elevenlabs"
    assert row["cost_usd"] == pytest.approx(0.30)


def test_log_elevenlabs_half_chars():
    tracker, mock_br = _make_tracker()
    tracker.log_elevenlabs(1, char_count=500)
    _, row = mock_br.create_row.call_args[0]
    assert row["cost_usd"] == pytest.approx(0.15)


def test_log_heygen_single_video():
    tracker, mock_br = _make_tracker()
    tracker.log_heygen(production_id=1)
    _, row = mock_br.create_row.call_args[0]
    assert row["service"] == "heygen"
    assert row["cost_usd"] == pytest.approx(0.50)


def test_log_heygen_two_videos():
    tracker, mock_br = _make_tracker()
    tracker.log_heygen(1, n_videos=2)
    _, row = mock_br.create_row.call_args[0]
    assert row["cost_usd"] == pytest.approx(1.00)


def test_log_fal_image():
    tracker, mock_br = _make_tracker()
    tracker.log_fal_image(1, n_images=3)
    _, row = mock_br.create_row.call_args[0]
    assert row["service"] == "fal"
    assert row["cost_usd"] == pytest.approx(0.075)


def test_log_fal_video_5s_tier():
    tracker, mock_br = _make_tracker()
    tracker.log_fal_video(1, n_clips=1, duration_s=5)
    _, row = mock_br.create_row.call_args[0]
    assert row["cost_usd"] == pytest.approx(0.50)


def test_log_fal_video_10s_tier():
    tracker, mock_br = _make_tracker()
    tracker.log_fal_video(1, n_clips=1, duration_s=10)
    _, row = mock_br.create_row.call_args[0]
    assert row["cost_usd"] == pytest.approx(1.00)


def test_log_fal_video_multiple_clips():
    tracker, mock_br = _make_tracker()
    tracker.log_fal_video(1, n_clips=6, duration_s=5)
    _, row = mock_br.create_row.call_args[0]
    assert row["cost_usd"] == pytest.approx(3.00)
