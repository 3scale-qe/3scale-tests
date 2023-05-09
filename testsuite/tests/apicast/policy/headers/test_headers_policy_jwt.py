"""
Rewrite spec/functional_specs/policies/header_policy_jwt_spec.rb

When the service is secured by OpenID and it uses header policy with liquid variables,
it should contain proper extra headers and the extra headers should contain correct info
from the JWT object
"""
import time
import pytest

from testsuite import rawobj
from testsuite.rhsso.rhsso import OIDCClientAuthHook
from testsuite.echoed_request import EchoedRequest


@pytest.fixture(scope="module", autouse=True)
def rhsso_setup(lifecycle_hooks, rhsso_service_info):
    """Have application/service with RHSSO auth configured"""

    lifecycle_hooks.append(OIDCClientAuthHook(rhsso_service_info, credentials_location="query"))


@pytest.fixture(scope="module")
def policy_settings():
    """
    Set the headers policy to add a header containing information from the JWT object
    """
    liquid_header = (
        "{% if jwt.typ== 'Bearer' %}{{ jwt.exp }};{{ jwt.iat }};{{ jwt.iss }};"
        "{{ jwt.aud }};{{ jwt.typ }};{{ jwt.azp }}{% else %}invalid{% endif %}"
    )

    return rawobj.PolicyConfig(
        "headers",
        {
            "response": [
                {"op": "set", "header": "X-RESPONSE-CUSTOM-JWT", "value": liquid_header, "value_type": "liquid"}
            ],
            "request": [
                {"op": "set", "header": "X-REQUEST-CUSTOM-JWT", "value": liquid_header, "value_type": "liquid"}
            ],
        },
    )


def test_headers_policy_extra_headers(api_client, rhsso_service_info, application):
    """
    Assert that
     - the request is successful
     - the request and the response contain the extra 'X-RESPONSE-CUSTOM-JWT' header
     - the extra 'X-RESPONSE-CUSTOM-JWT' headers contain the correct values
    """
    token = rhsso_service_info.access_token(application)
    client = api_client()

    # Auth session needs to be None when we are testing access_token
    client.auth = None
    response = client.get("/get", params={"access_token": token})
    assert response.status_code == 200

    echoed_request = EchoedRequest.create(response)
    assert echoed_request.params["access_token"] == token
    assert "X-RESPONSE-CUSTOM-JWT" in response.headers
    assert response.headers["X-RESPONSE-CUSTOM-JWT"] == echoed_request.headers["X-Request-Custom-Jwt"]
    assert echoed_request.headers["X-Request-Custom-Jwt"] != "invalid"

    exp, iat, iss, _, _, azp = response.headers["X-RESPONSE-CUSTOM-JWT"].split(";")

    # add 10 seconds to now because there can be different times
    # in Jenkins machine and machine with Apicast
    now = time.time() + 10
    assert rhsso_service_info.issuer_url() == iss
    assert azp == application["application_id"]
    assert float(exp) > now
    assert float(iat) <= now
