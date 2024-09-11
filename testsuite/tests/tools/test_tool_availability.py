"""Tests availability of the tools with public route"""

import json

import requests
import pytest

from testsuite.rhsso import RHSSOServiceConfiguration


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


def test_sso_availability(rhsso_kind, rhsso_service_info: RHSSOServiceConfiguration):
    """
    Sends get request to project sso endpoint '/health' for rhbk and /auth for rhsso
    Asserts that:
        - sso is running and endpoint returns 200
        - for rhbk also asserts that the status is UP
    """
    endpoint = rhsso_service_info.rhsso.server_url
    if rhsso_kind == "rhbk":
        endpoint = endpoint + "/health"
    response = requests.get(endpoint, verify=False)
    assert response.status_code == 200
    if rhsso_kind == "rhbk":
        status = json.loads(response.text)["status"]
        assert status == "UP"
