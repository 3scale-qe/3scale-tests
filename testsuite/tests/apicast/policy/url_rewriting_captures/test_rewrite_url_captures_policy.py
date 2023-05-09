"""
Rewrite spec/functional_specs/policies/url_rewrite/url_rewrite_capture_spec.rb
"""
import pytest

from testsuite import rawobj
from testsuite.echoed_request import EchoedRequest


@pytest.fixture(scope="module")
def policy_settings():
    """
    Set policy settings
    """
    return rawobj.PolicyConfig(
        "rewrite_url_captures",
        {
            "transformations": [
                {"match_rule": "/{var_1}/{var_2}", "template": "/{var_2}?my_arg={var_1}"},
                {"match_rule": "/{var_1}/{var_2}", "template": "/my_arg={var_2}?my_arg2={var_1}"},
            ]
        },
    )


def test_rewrite_url_captures(api_client):
    """must match first rule and rewrite path /hello/get to /get?my_arg=hello"""
    response = api_client().get("/hello/get")
    assert response.status_code == 200

    echoed_request = EchoedRequest.create(response)
    assert echoed_request.params["my_arg"] == "hello"
    assert echoed_request.path == "/get"
