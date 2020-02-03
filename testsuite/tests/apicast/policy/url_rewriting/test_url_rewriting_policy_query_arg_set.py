"""
Rewrite spec/functional_specs/policies/url_rewrite_query/query_rewrite_policy_set_spec.rb
"""

import pytest

from testsuite import rawobj
from testsuite.echoed_request import EchoedRequest


@pytest.fixture(scope="module")
def policy_settings():
    """Add url_rewriting_append policy"""
    return rawobj.PolicyConfig("url_rewriting", {
        "query_args_commands": [{"op": "set", "arg": "new_arg", "value": "new_value"},
                                {"op": "set", "arg": "arg", "value": "value"}]})


def test_url_rewriting_policy_query_set_args(api_client):
    """Args should be rewritten for the request"""
    response = api_client.get("/get", params=dict(arg="old_value"))
    echoed_request = EchoedRequest.create(response)

    assert response.status_code == 200
    assert echoed_request.params["arg"] == "value"
    assert echoed_request.params["new_arg"] == "new_value"
