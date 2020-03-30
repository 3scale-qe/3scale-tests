"""
Rewrite spec/functional_specs/policies/header_policy_jwt_spec.rb
"""
import time
import pytest
from threescale_api.resources import Service

from testsuite import rawobj
from testsuite.rhsso.rhsso import OIDCClientAuth
from testsuite.echoed_request import EchoedRequest


@pytest.fixture(scope="module")
def service_settings(service_settings):
    "Set auth mode to OIDC"
    service_settings.update(backend_version=Service.AUTH_OIDC)
    return service_settings


@pytest.fixture(scope="module")
def service_proxy_settings(rhsso_service_info, service_proxy_settings):
    "Set OIDC issuer and type"
    service_proxy_settings.update(
        {"credentials_location": "query"},
        oidc_issuer_endpoint=rhsso_service_info.authorization_url(),
        oidc_issuer_type="keycloak")
    return service_proxy_settings


@pytest.fixture(scope="module")
def service(service):
    "Update OIDC configuration and policy settings"
    service.proxy.oidc.update(params={
        "oidc_configuration": {
            "standard_flow_enabled": False,
            "direct_access_grants_enabled": True
        }})

    return service


@pytest.fixture(scope="module")
def policy_settings():
    "Set policy settings"
    liquid_header = "{% if jwt.typ== \'Bearer\' %}{{ jwt.exp }};{{ jwt.nbf }};{{ jwt.iat }};{{ jwt.iss }};" \
                    "{{ jwt.aud }};{{ jwt.typ }};{{ jwt.azp }};{{ jwt.auth_time }}{% else %}invalid{% endif %}"

    return rawobj.PolicyConfig("headers", {
        "response": [{"op": "set", "header": "X-RESPONSE-CUSTOM-JWT", "value": liquid_header, "value_type": "liquid"}],
        "request": [{"op": "set", "header": "X-REQUEST-CUSTOM-JWT", "value": liquid_header, "value_type": "liquid"}],
    })


@pytest.fixture(scope="module")
def application(rhsso_service_info, application):
    "Add OIDC client authentication"
    application.register_auth("oidc", OIDCClientAuth(rhsso_service_info))
    return application


def test_headers_policy_extra_headers(api_client, rhsso_service_info, application):
    "Test should succeed on staging gateway with proper extra headers"
    app_key = application.keys.list()["keys"][0]["key"]["value"]
    token = rhsso_service_info.password_authorize(application["client_id"], app_key).token['access_token']

    # pylint: disable=protected-access
    # Auth session needs to be None when we are testing access_token
    api_client._session.auth = None
    response = api_client.get("/get", params={'access_token': token})
    echoed_request = EchoedRequest.create(response)
    assert response.status_code == 200
    assert echoed_request.params["access_token"] == token
    assert "X-RESPONSE-CUSTOM-JWT" in response.headers
    assert response.headers["X-RESPONSE-CUSTOM-JWT"] == echoed_request.headers["X-Request-Custom-Jwt"]
    assert echoed_request.headers["X-Request-Custom-Jwt"] != "invalid"


# For JWT details see https://www.iana.org/assignments/jwt/jwt.xhtml
# jwt.exp; jwt.nbf; jwt.iat; jwt.iss; jwt.aud; jwt.typ; jwt.azp; jwt.auth_time
@pytest.mark.flaky
def test_headers_policy_extra_headers_jwt(api_client, rhsso_service_info, application):
    "Test should contain extra header with correct info from JWT object"
    app_key = application.keys.list()["keys"][0]["key"]["value"]
    token = rhsso_service_info.password_authorize(application["client_id"], app_key).token['access_token']

    response = api_client.get("/get", params={'access_token': token})
    exp, nbf, iat, iss, _, _, azp, auth_time = response.headers["X-RESPONSE-CUSTOM-JWT"].split(";")

    # add 10 seconds to now because there can be different times
    # in Jenkins machine and machine with Apicast
    now = time.time() + 10
    assert float(exp) > now
    assert float(nbf) <= now
    assert float(iat) <= now
    assert float(auth_time) <= now
    assert rhsso_service_info.issuer_url() == iss
    assert azp == application["application_id"]
