"""Tests availability of the tools with public route"""

import requests
import pytest


def test_prometheus_availability(prometheus):
    """
    Sends get request to project Prometheus endpoint '/api/v1/status/runtimeinfo'
    Asserts that:
        - Prometheus is running and returns 200
    """
    assert prometheus.is_available()


@pytest.mark.parametrize(
    ("tool_name", "endpoint"),
    [
        ("echo_api", ""),
        ("go-httpbin", ""),
        ("go-httpbin+ssl", ""),
        ("jaeger-query", ""),
        ("jaeger-query+ssl", ""),
        ("mockserver", ""),
        ("mockserver+ssl", ""),
        ("minio", "/minio/health/live"),
        ("minio+ssl", "/minio/health/live"),
    ],
)
def test_tool_availability(private_base_url, tool_name, endpoint):
    """
    Sends a get request on a given tool.
    Asserts that:
        - given tool is running and returns 200
    """
    endpoint = private_base_url(tool_name) + endpoint
    response = requests.head(endpoint, verify=False)
    assert response.status_code == 200
