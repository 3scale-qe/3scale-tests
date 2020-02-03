"""
Rewrite spec/functional_specs/policies/url_rewrite_query/query_rewrite_policy_del_spec.rb
"""

import pytest

from testsuite import rawobj
from testsuite.echoed_request import EchoedRequest


@pytest.fixture(scope="module")
def policy_settings():
    """Add url_rewriting_append policy"""
    return rawobj.PolicyConfig("url_rewriting", {
        "query_args_commands": [{"op": "delete", "arg": "arg"}]})


def test_url_rewriting_policy_delete_arg_req(api_client):
    """Args should be deleted for the request"""
    response = api_client.get("/get", params=dict(arg="old_value", arg2="value"))
    echoed_request = EchoedRequest.create(response)

    assert response.status_code == 200
    assert 'arg' not in echoed_request.params
    assert echoed_request.params['arg2'] == "value"
