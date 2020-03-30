"""
Testing proper function of adding liquid headers when no previous liquid header exists.

Rewrite: ./spec/functional_specs/policies/headers/header_policy_liquid_set_spec.rb
"""

import pytest
from testsuite import rawobj
from testsuite.echoed_request import EchoedRequest


@pytest.fixture(scope="module")
def policy_settings():
    """configures headers in policy"""
    return rawobj.PolicyConfig("headers", {
        "response": [{"op": "set",
                      "header": "X-RESPONSE-LIQUID-SET",
                      "value_type": "liquid",
                      "value": "Service_id {{ service.id }}"
                      }],
        "request": [{"op": "set",
                     "header": "X-REQUEST-NO-LIQUID-SET",
                     "value": "Service_id {{ service.id }}"
                     }]})


def test_header_policy_add_to_response_with_liquid_service_id_api_client(api_client, service):
    """must add header to response using the liquid - service id should be expanded"""
    liquid_value = f"Service_id {service.entity_id}"
    response = api_client.get("/get")

    assert "X-response-liquid-set" in response.headers
    assert response.headers["X-response-liquid-set"] == liquid_value


def test_header_policy_add_to_request_without_liquid_service_id(application):
    """must add header to request without using the liquid - service id should not be expanded"""
    value = "Service_id {{ service.id }}"
    response = application.test_request()
    echoed_request = EchoedRequest.create(response)

    assert "X-request-no-liquid-set" in echoed_request.headers
    assert echoed_request.headers["x-request-no-liquid-set"] == value
