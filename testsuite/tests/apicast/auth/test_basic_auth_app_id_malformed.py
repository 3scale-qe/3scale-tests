"""
Test malformed Basic Auth headers with app_id/app_key authentication.
Tests against both SystemApicast and SelfManagedApicast gateways.

Related issue: https://issues.redhat.com/browse/THREESCALE-11435
"""

import pytest
from packaging.version import Version
from threescale_api.resources import Service

from testsuite import TESTED_VERSION
from testsuite.capabilities import Capability
from testsuite.gateways import gateway
from testsuite.gateways.apicast.selfmanaged import SelfManagedApicast
from testsuite.gateways.apicast.system import SystemApicast
from testsuite.httpx import HttpxClient
from testsuite.utils import basic_auth_string, blame


@pytest.fixture(
    scope="module",
    params=[
        SystemApicast,
        pytest.param(SelfManagedApicast, marks=pytest.mark.required_capabilities(Capability.CUSTOM_ENVIRONMENT)),
    ],
)
def gateway_kind(request):
    """Gateway class to use for malformed test."""
    return request.param


@pytest.fixture(scope="module")
def staging_gateway(request, gateway_kind, testconfig):
    """Deploy gateway for malformed test."""
    gw = gateway(kind=gateway_kind, staging=True, name=blame(request, "gw"))
    if not testconfig["skip_cleanup"]:
        request.addfinalizer(gw.destroy)
    gw.create()
    return gw


@pytest.fixture(scope="module")
def service_settings(request, gateway_kind):  # pylint: disable=unused-argument
    """Service settings for malformed test - depends on gateway_kind for separate instances."""
    return {"name": blame(request, "svc"), "backend_version": Service.AUTH_APP_ID_KEY}


@pytest.fixture(scope="module")
def service_proxy_settings(service_proxy_settings):
    """Set credentials location to 'authorization' (Basic HTTP auth)."""
    service_proxy_settings.update(credentials_location="authorization")
    return service_proxy_settings


@pytest.fixture(scope="module")
def http_client(application):
    """HTTP client for malformed test."""
    client = HttpxClient(False, application)
    client.auth = None
    yield client
    client.close()


@pytest.fixture(scope="module")
def valid_auth_headers(application):
    """Generate valid Basic Auth headers for malformed test."""
    creds = application.authobj().credentials
    authorization = basic_auth_string(creds["app_id"], creds["app_key"])
    return {"Authorization": authorization}


@pytest.fixture(scope="module")
def invalid_auth_headers():
    """Generate malformed Basic Auth headers for testing."""
    return {"Authorization": "Basic test123?"}


@pytest.mark.skipif(TESTED_VERSION < Version("2.14"), reason="TESTED_VERSION < Version('2.14')")
@pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-11435")
def test_basic_auth_malformed_secret(http_client, valid_auth_headers, invalid_auth_headers):
    """Test that APIcast rejects malformed Basic Auth headers with 403 while accepting valid credentials."""
    # Valid request
    response = http_client.get("/get", headers=valid_auth_headers)
    assert response.status_code == 200, "Valid request failed unexpectedly."

    # Malformed request
    response = http_client.get("/get", headers=invalid_auth_headers)
    assert response.status_code == 403, "Malformed request did not return 403 as expected."
