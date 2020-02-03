"""
Testing service authentication using OIDC with RHSSO
"""
import pytest
from threescale_api.resources import Service

from testsuite.rhsso.rhsso import OIDCClientAuth


@pytest.fixture(scope="module")
def service_settings(service_settings):
    "Set auth mode to OIDC"
    service_settings.update(backend_version=Service.AUTH_OIDC)
    return service_settings


@pytest.fixture(scope="module")
def service_proxy_settings(rhsso_service_info, service_proxy_settings):
    "Set OIDC issuer and type"
    service_proxy_settings.update(
        oidc_issuer_endpoint=rhsso_service_info.authorization_url(),
        oidc_issuer_type="keycloak")
    return service_proxy_settings


@pytest.fixture(scope="module")
def service(service):
    "Update OIDC configuration"
    service.proxy.oidc.update(params={
        "oidc_configuration": {
            "standard_flow_enabled": False,
            "direct_access_grants_enabled": True
        }
    })
    return service


@pytest.fixture(scope="module")
def application(rhsso_service_info, application):
    "Add OIDC client authentication"
    application.register_auth("oidc", OIDCClientAuth(rhsso_service_info))
    return application


def test_rhsso_auth(api_client):
    """Check if OIDC connect using RHSSO works"""
    response = api_client.get("/get")
    assert response.status_code == 200


def test_rhsso_no_auth(application, testconfig):
    """Check if OIDC connect without auth won't work"""
    client = application.api_client(verify=testconfig["ssl_verify"])
    # pylint: disable=protected-access
    client._session.auth = None
    response = client.get("/get")

    assert response.status_code == 403
