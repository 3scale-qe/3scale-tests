"""Conftest for jwt claim check policy"""
import pytest
from threescale_api.resources import Service


@pytest.fixture(scope="module")
def service_settings(service_settings):
    """Set auth mode to OIDC"""
    service_settings.update(backend_version=Service.AUTH_OIDC)
    return service_settings


@pytest.fixture(scope="module")
def service_proxy_settings(rhsso_service_info, service_proxy_settings):
    """Set OIDC issuer and type"""
    service_proxy_settings.update(
        {"credentials_location": "query"},
        oidc_issuer_endpoint=rhsso_service_info.authorization_url(),
        oidc_issuer_type="keycloak")
    return service_proxy_settings


@pytest.fixture(scope="module")
def service(service):
    """Update OIDC configuration and policy settings"""
    service.proxy.oidc.update(params={
        "oidc_configuration": {
            "standard_flow_enabled": False,
            "direct_access_grants_enabled": True
        }})

    return service
