"""Tests du module formatter."""
import pytest

from app.formatter import format_metrics


def _sample_metrics() -> dict:
    return {
        "timestamp": "2026-08-27T12:00:00+00:00",
        "hostname": "server-01",
        "cpu": {"percent": 10.0, "logical_cores": 4},
        "memory": {
            "total_bytes": 1000,
            "available_bytes": 500,
            "used_bytes": 500,
            "percent": 50.0,
        },
        "system": {"load_1m": 0.1, "load_5m": 0.2, "load_15m": 0.3},
    }


def test_format_metrics_ok():
    payload = format_metrics(_sample_metrics())
    assert payload["agent"] == "system-metrics-agent"
    assert payload["event_type"] == "system_metrics"
    assert payload["data"]["hostname"] == "server-01"


def test_format_metrics_custom_agent_name():
    payload = format_metrics(_sample_metrics(), agent_name="mon-agent")
    assert payload["agent"] == "mon-agent"


def test_format_metrics_incomplete_raises():
    incomplete = {"timestamp": "x", "hostname": "h"}
    with pytest.raises(ValueError, match="incomplètes"):
        format_metrics(incomplete)
