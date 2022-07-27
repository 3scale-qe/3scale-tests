"""
Tests that the liquid context debug policy is active on products
with multiple backends.
"""
from urllib.parse import urlparse

import pytest


pytestmark = [pytest.mark.require_version("2.11"),
              pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-6312")]


@pytest.fixture(scope="module")
def backend_bin(custom_backend, private_base_url):
    """Httpbin backend"""
    return custom_backend("backend_bin", endpoint=private_base_url("httpbin"))


@pytest.fixture(scope="module")
def backend_echo(custom_backend, private_base_url):
    """Echo-api backend"""
    return custom_backend("backend_echo", endpoint=private_base_url("echo_api"))


@pytest.fixture(scope="module")
def backends_mapping(backend_bin, backend_echo):
    """
    Create 2 separate backends for the product:
        - path to Backend echo: "/echo"
        - path to Backend httpbin: "/bin"
    """
    return {"/echo": backend_echo, "/bin": backend_bin}


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
        - contains uri value "/" -  set at https://github.com/3scale/APIcast/
        blob/3eac1272b66817dfcf2d7cfdc8ed779cf934caeb/gateway/src/apicast/policy/routing/upstream_selector.lua#L43
        - contains host with proper value
        - contains used http method
        - contains used access token
        - contains header object
        - contains remote address
        - contains JWT object
    """
    client = api_client()
    client.auth = None

    response = client.get('/echo/anything/echo', params={'access_token': access_token})
    assert response.status_code == 200

    jrequest = response.json()
    parsed_url = urlparse(service.proxy.list()['sandbox_endpoint'])

    assert "uri" in jrequest
    assert jrequest["uri"] == "/"
    assert jrequest["host"] == parsed_url.hostname
    assert jrequest["http_method"] == "GET"
    assert jrequest["current"]["original_request"]["current"]["query"] ==\
        "access_token=" + access_token

    assert "headers" in jrequest
    assert "remote_addr" in jrequest
    assert "jwt" in jrequest["current"]
