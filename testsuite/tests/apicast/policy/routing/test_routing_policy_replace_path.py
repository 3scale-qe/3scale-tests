"""
    Test that checks if the first anything part is removed
"""

import pytest
from testsuite import rawobj
from testsuite.echoed_request import EchoedRequest


@pytest.fixture(scope="module")
def service(service, private_base_url):
    """
    Sets routing policy configuration to service
    routes by patch matching and is using 'replace_path' to modify path if matched
    """
    routing_policy_op = {"operations": [{"op": "==", "value": "/anything/anything", "match": "path"}]}
    proxy = service.proxy.list()
    proxy.policies.insert(
        0,
        rawobj.PolicyConfig(
            "routing",
            {
                "rules": [
                    {
                        "url": private_base_url(),
                        "condition": routing_policy_op,
                        "replace_path": "{{ original_request.path | remove_first: '/anything' }}",
                    }
                ]
            },
        ),
    )

    return service


@pytest.mark.smoke
@pytest.mark.issue("https://issues.jboss.org/browse/THREESCALE-3593")
def test_routing_policy_replace_path(api_client):
    """
    Test that checks if the first anything part is removed
    """
    response = api_client().get("/anything/anything")
    assert response.status_code == 200

    echoed_request = EchoedRequest.create(response)
    assert echoed_request.path == "/anything"
