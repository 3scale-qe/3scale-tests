"""Test Financial-Grade API policy with oauth2 certificate bound access token (advanced profile)"""

import pytest
import requests

from testsuite import rawobj
from testsuite.utils import blame, warn_and_skip
from testsuite.rhsso import OIDCClientAuth, OIDCClientAuthHook
from testsuite.certificates import Certificate

# pylint: disable=reimported, unused-import
# flake8: noqa
from testsuite.tests.apicast.policy.tls.conftest import (
    certificate,
    manager,
    superdomain,
    server_authority,
    staging_gateway,
    gateway_options,
    gateway_environment,
    valid_authority,
    create_cert,
)


@pytest.fixture(scope="module")
def mtls_client_cert(request, testconfig):
    """Clients certificate. CA of this cert needs to be trusted by the sso"""
    try:
        crt = testconfig["shared_certs"]["client_certs"]["valid"][0]
    except IndexError:
        warn_and_skip("Valid tools cert is not available, skipping fapi advanced tests")
    cert = Certificate(crt["key"], crt["crt"])
    if not testconfig["skip_cleanup"]:
        request.addfinalizer(cert.delete_files)
    return cert.files["certificate"], cert.files["key"]


# flake8: noqa
@pytest.fixture()
def unknown_cert(certificate):
    """Cert which won't be used for obtaining the token"""
    return certificate.files["certificate"], certificate.files["key"]


@pytest.fixture(scope="module")
def service(service):
    """
    Set fapi policy in advanced configuration for the service

    policy order:
        3scale APIcast
        Fapi
    """
    fapi_policy = rawobj.PolicyConfig(
        "fapi",
        configuration={
            "validate_x_fapi_customer_ip_address": True,
            "validate_oauth2_certificate_bound_access_token": True,
        },
    )
    service.proxy.list().policies.insert(1, fapi_policy)
    return service


@pytest.fixture(scope="module")
def fapi_sso_client_id():
    """Client_id in the SSO and app_id of the application in 3scale must be the same"""
    return "fapi_sso_client"


# pylint: disable=too-many-arguments
@pytest.fixture(scope="module")
def application(
    service, custom_application, custom_app_plan, lifecycle_hooks, request, fapi_sso_client_id, rhsso_service_info
):
    """application bound to the account and service existing over whole testing session"""
    plan = custom_app_plan(rawobj.ApplicationPlan(blame(request, blame(request, "fapi"))), service)
    app = custom_application(
        rawobj.Application(name=fapi_sso_client_id, app_id=fapi_sso_client_id, application_plan=plan),
        hooks=lifecycle_hooks,
    )
    service.proxy.deploy()
    app.register_auth("oidc", OIDCClientAuth.partial(rhsso_service_info))
    return app


@pytest.fixture(scope="module")
def fapi_sso_client(rhsso_service_info, fapi_sso_client_id, mtls_client_cert):
    """Create client in SSO with mtls enabled. SSO will authorize any client with cert signed by
    accepted CA with any subjectdn"""
    client_config = {
        "clientAuthenticatorType": "client-x509",
        "directAccessGrantsEnabled": True,
        "serviceAccountsEnabled": True,
        "authorizationServicesEnabled": True,
        "publicClient": False,
        "protocol": "openid-connect",
        "attributes": {
            "token.endpoint.auth.method": "tls_client_auth",
            "x509.subjectdn": "(.*?)(?:$)",
            "tls.client.certificate.bound.access.tokens": "true",
            "client.authentication.type": "tls",
            "x509.allow.regex.pattern.comparison": "true",
        },
    }
    return rhsso_service_info.realm.create_client(fapi_sso_client_id, cert=mtls_client_cert, **client_config)


# pylint: disable=too-few-public-methods
class FapiClient:
    """Temporary class for sending requests to apicast. This should be replaced by using fixture api_client"""

    def __init__(self, base_url, verify):
        self.base_url = base_url
        self.http_session = requests.Session()
        self.http_session.verify = verify

    def get(self, path="/", headers=None, token=None, cert=None):
        """Sends http get request to url which was set up during initialization"""
        if headers is None:
            headers = {}
        if token:
            headers.update({"authorization": "Bearer " + token})
        return self.http_session.get(self.base_url + path, headers=headers, cert=cert)


@pytest.fixture()
def fapi_api_client(application):
    """Create client for api_calls on apicast"""
    # pylint: disable=protected-access
    api_base_url = application.api_client()._base_url
    return FapiClient(api_base_url, verify=False)


@pytest.fixture(scope="module", autouse=True)
def rhsso_setup(lifecycle_hooks, rhsso_service_info):
    """Have application/service with RHSSO auth configured"""
    lifecycle_hooks.append(OIDCClientAuthHook(rhsso_service_info))


def test_valid_cert_returns_200(fapi_api_client, fapi_sso_client, mtls_client_cert):
    """
    Test client authentication using certificate bound access token (https://datatracker.ietf.org/doc/html/rfc8705).

    Obtain client certificate bound access token.
    Using the same certificate and obtained token send request to staging apicast.
    Assert, that response contains http return code 200
    """
    mtls_client = fapi_sso_client.oidc_client
    api_access_token = mtls_client.token(grant_type="client_credentials")["access_token"]
    response = fapi_api_client.get(token=api_access_token, cert=mtls_client_cert)
    assert response.status_code == 200


def test_invalid_cert_returns_401(fapi_api_client, fapi_sso_client, unknown_cert):
    """
    Test client authentication using certificate bound access token (https://datatracker.ietf.org/doc/html/rfc8705).

    Obtain client certificate bound access token.
    Using the different certificate and obtained token send request to staging apicast.
    Assert, that response contains http return code 401
    """
    mtls_client = fapi_sso_client.oidc_client
    api_access_token = mtls_client.token(grant_type="client_credentials")["access_token"]
    response = fapi_api_client.get(token=api_access_token, cert=unknown_cert)
    assert response.status_code == 401
