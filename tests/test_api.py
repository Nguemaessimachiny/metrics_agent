"""Tests de l'API FastAPI."""
from fastapi.testclient import TestClient

from app.api import app, received_metrics

client = TestClient(app)


def setup_function():
    """Vide le stockage en mémoire avant chaque test."""
    received_metrics.clear()


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_receive_metrics():
    payload = {
        "agent": "system-metrics-agent",
        "event_type": "system_metrics",
        "data": {"cpu": {"percent": 1.0}},
    }
    response = client.post("/metrics", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "received"
    assert body["total_received"] == 1


def test_latest_metrics_empty():
    response = client.get("/metrics/latest")
    assert response.status_code == 404


def test_latest_metrics_after_post():
    payload = {
        "agent": "system-metrics-agent",
        "event_type": "system_metrics",
        "data": {"hostname": "h1"},
    }
    client.post("/metrics", json=payload)
    response = client.get("/metrics/latest")
    assert response.status_code == 200
    assert response.json()["agent"] == "system-metrics-agent"
    assert response.json()["data"]["hostname"] == "h1"


def test_get_all_metrics():
    client.post(
        "/metrics",
        json={
            "agent": "a1",
            "event_type": "system_metrics",
            "data": {},
        },
    )
    response = client.get("/metrics")
    assert response.status_code == 200
    assert response.json()["total"] == 1
