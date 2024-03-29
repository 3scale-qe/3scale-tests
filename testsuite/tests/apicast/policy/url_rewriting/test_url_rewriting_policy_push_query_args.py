"""
Rewrite spec/functional_specs/policies/url_rewrite_query/query_rewrite_policy_push_spec.rb
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
        "url_rewriting",
        {
            "query_args_commands": [
                {"op": "push", "arg": "new_arg", "value": "new_value"},
                {"op": "push", "arg": "arg", "value": "value"},
            ]
        },
    )


def test_url_rewriting_push_query_args(api_client):
    """
    Check if request rewrite query args
    """
    client = api_client()
    response = client.get("/get", params={"arg": "old_value"})
    assert response.status_code == 200

    echoed_request = EchoedRequest.create(response)
    assert echoed_request.params.get("arg") == ["old_value", "value"]
    assert echoed_request.params.get("new_arg") == "new_value"
