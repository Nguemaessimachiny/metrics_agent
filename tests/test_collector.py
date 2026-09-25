"""Tests du module collector."""
from unittest.mock import MagicMock, patch

import pytest

from app.collector import MetricsCollectionError, collect_system_metrics, get_load_average


def test_get_load_average_on_windows():
    with patch("app.collector.platform.system", return_value="Windows"):
        result = get_load_average()
    assert result == {
        "load_1m": None,
        "load_5m": None,
        "load_15m": None,
    }


def test_get_load_average_parses_uptime():
    fake = MagicMock()
    fake.stdout = " 12:00:00 up 1 day,  1:00,  1 user,  load average: 0.10, 0.20, 0.30\n"
    with (
        patch("app.collector.platform.system", return_value="Linux"),
        patch("app.collector.subprocess.run", return_value=fake),
    ):
        result = get_load_average()
    assert result == {"load_1m": 0.1, "load_5m": 0.2, "load_15m": 0.3}


def test_get_load_average_command_missing():
    with (
        patch("app.collector.platform.system", return_value="Linux"),
        patch("app.collector.subprocess.run", side_effect=FileNotFoundError()),
    ):
        with pytest.raises(MetricsCollectionError, match="uptime"):
            get_load_average()


def test_collect_system_metrics_ok():
    memory = MagicMock(
        total=1000,
        available=400,
        used=600,
        percent=60.0,
    )
    with (
        patch("app.collector.psutil.virtual_memory", return_value=memory),
        patch("app.collector.psutil.cpu_percent", return_value=12.5),
        patch("app.collector.psutil.cpu_count", return_value=8),
        patch(
            "app.collector.get_load_average",
            return_value={"load_1m": 0.1, "load_5m": 0.2, "load_15m": 0.3},
        ),
        patch("app.collector.platform.node", return_value="host-test"),
    ):
        metrics = collect_system_metrics()

    assert metrics["hostname"] == "host-test"
    assert metrics["cpu"]["percent"] == 12.5
    assert metrics["memory"]["percent"] == 60.0
    assert "timestamp" in metrics
