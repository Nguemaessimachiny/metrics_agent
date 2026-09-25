"""Tests du module sender."""
from unittest.mock import MagicMock, patch

import pytest
import requests

from app.sender import MetricsDeliveryError, send_metrics


def test_send_metrics_success():
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = {"status": "received"}
    mock_response.raise_for_status.return_value = None

    with patch("app.sender.requests.post", return_value=mock_response) as mock_post:
        result = send_metrics(
            "http://example.com/metrics",
            {"agent": "test"},
            timeout=2,
        )

    mock_post.assert_called_once()
    assert result["status_code"] == 201
    assert result["response"]["status"] == "received"


def test_send_metrics_http_error():
    with patch(
        "app.sender.requests.post",
        side_effect=requests.ConnectionError("down"),
    ):
        with pytest.raises(MetricsDeliveryError, match="Échec de l'envoi"):
            send_metrics("http://example.com/metrics", {"agent": "test"})
