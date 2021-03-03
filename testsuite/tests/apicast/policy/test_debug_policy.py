"""
Testing the liquid context debug policy
Rewrite: ./spec/functional_specs/policies/debug_policy_spec.rb
"""

from urllib.parse import urlparse
import pytest

from testsuite import rawobj
from testsuite.rhsso.rhsso import OIDCClientAuthHook


@pytest.fixture(scope="module", autouse=True)
def rhsso_setup(lifecycle_hooks, rhsso_service_info):
    """Have application/service with RHSSO auth configured"""

    lifecycle_hooks.append(OIDCClientAuthHook(rhsso_service_info, "query"))


@pytest.fixture(scope="module")
def service(service):
    "Service with prepared policy_settings added"
    service.proxy.list().policies.insert(0, rawobj.PolicyConfig("liquid_context_debug", {}))
    return service


@pytest.fixture(scope="module")
def access_token(application, rhsso_service_info):
    """get rhsso access token"""
    app_key = application.keys.list()["keys"][0]["key"]["value"]
    return rhsso_service_info.password_authorize(application["client_id"],
                                                 app_key).token['access_token']


def test_debug_policy(api_client, access_token, service):
    """
    Test the liquid context debug policy:
        - Add the liquid_context_debug_policy
        - Set this policy to the first place in the policy chain
        - Send request using rhsso OIDC authentication
        - Response should include objects from https://github.com/3scale/
          apicast/blob/master/gateway/src/apicast/policy/ngx_variable.lua#L6
          and JWT object

    Test if:
        - return code is 200
        - contains uri with proper value (get)
        - contains host with proper value
        - contains used http method
        - contains used access token
        - contains header object
        - contains remote address
        - contains JWT object
    """
    client = api_client()
    client.auth = None

    response = client.get('/get', params={'access_token': access_token})
    assert response.status_code == 200

    jrequest = response.json()
    parsed_url = urlparse(service.proxy.list()['sandbox_endpoint'])

    assert jrequest["uri"] == "/get"
    assert jrequest["host"] == parsed_url.hostname
    assert jrequest["http_method"] == "GET"
    assert jrequest["current"]["original_request"]["current"]["query"] ==\
        "access_token=" + access_token

    assert "headers" in jrequest
    assert "remote_addr" in jrequest
    assert "jwt" in jrequest["current"]
