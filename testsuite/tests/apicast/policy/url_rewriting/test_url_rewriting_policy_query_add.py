"""
Rewrite spec/functional_specs/policies/url_rewrite_query/query_rewrite_policy_add_spec.rb
"""

import pytest

from testsuite import rawobj
from testsuite.echoed_request import EchoedRequest


@pytest.fixture(scope="module")
def policy_settings():
    """
    Add the 'url_rewriting' policy to policy chain with following settings
    """
    return rawobj.PolicyConfig(
        "url_rewriting",
        {
            "query_args_commands": [
                {"op": "add", "arg": "new_arg", "value": "new_value"},
                {"op": "add", "arg": "arg", "value": "value"},
            ]
        },
    )


def test_url_rewriting_add_query_args(api_client):
    """
    Make request with parameter 'arg' with value 'value'
    Check if the 'value' has been added to the 'arg' parameter
    Check if parameter 'new_arg' has not been created
    """
    client = api_client()
    response = client.get("/get", params={"arg": "old_value"})
    assert response.status_code == 200

    echoed_request = EchoedRequest.create(response)
    assert echoed_request.params.get("arg") == ["old_value", "value"]
    assert echoed_request.params.get("new_arg") != "new_value"
