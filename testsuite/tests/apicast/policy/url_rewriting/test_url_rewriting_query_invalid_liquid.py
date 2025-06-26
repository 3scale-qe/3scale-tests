"""
Rewrite spec/functional_specs/policies/url_rewrite_query/query_rewrite_policy_invalid_liquid_spec.rb
"""

import pytest

from testsuite import rawobj
from testsuite.echoed_request import EchoedRequest


@pytest.fixture(scope="module")
def policy_settings():
    """Set policy settings"""
    return rawobj.PolicyConfig(
        "url_rewriting",
        {
            "query_args_commands": [
                {"op": "set", "arg": "invalid", "value_type": "liquid", "value": "{{ now() }}"},
                {"op": "set", "arg": "valid", "value_type": "liquid", "value": "{{ uri }}"},
            ]
        },
    )


def test_url_rewriting_query_liquid(api_client):
    """Test for valid and invalid liquid tag"""
    response = api_client().get("/get")
    assert response.status_code == 200
    echoed_request = EchoedRequest.create(response)
    assert echoed_request.params["valid"] == "/get"
    assert echoed_request.params["invalid"] == ""
