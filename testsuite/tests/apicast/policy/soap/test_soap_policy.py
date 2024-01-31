"""
Rewrite spec/functional_specs/policies/soap/soap_policy_spec.rb
"""

import pytest
from testsuite import rawobj
from testsuite import resilient


@pytest.fixture(scope="module")
def policy_settings():
    """Set policy settings"""
    mapping_rules = [
        {"pattern": "soap_policy_action", "metric_system_name": "hits", "delta": "3"},
        {"pattern": "soap_policy_ctype", "metric_system_name": "hits", "delta": "5"},
    ]
    return rawobj.PolicyConfig("soap", {"mapping_rules": mapping_rules})


def test_soap_policy_action(api_client, application):
    "Tests if 3scale report correct usage with SOAPAction header"
    analytics = application.threescale_client.analytics
    usage_before = analytics.list_by_service(application["service_id"], metric_name="hits")["total"]
    api_client().get("/get", headers={"Soapaction": "soap_policy_action"})
    usage_after = resilient.analytics_list_by_service(
        application.threescale_client, application["service_id"], "hits", "total", usage_before + 1
    )
    assert usage_after == usage_before + 4


def test_soap_policy_ctype(api_client, application):
    "Tests if 3scale report correct usage with Content-Type header"
    analytics = application.threescale_client.analytics
    usage_before = analytics.list_by_service(application["service_id"], metric_name="hits")["total"]
    api_client().get("/get", headers={"Content-Type": "application/soap+xml;action=soap_policy_ctype"})
    usage_after = resilient.analytics_list_by_service(
        application.threescale_client, application["service_id"], "hits", "total", usage_before + 1
    )
    assert usage_after == usage_before + 6


def test_soap_policy_action_ctype(api_client, application):
    "Tests if 3scale report correct usage with both SOAPAction and Content-Type headers"
    analytics = application.threescale_client.analytics
    usage_before = analytics.list_by_service(application["service_id"], metric_name="hits")["total"]
    api_client().get(
        "/get",
        headers={"Soapaction": "soap_policy_action", "Content-Type": "application/soap+xml;action=soap_policy_ctype"},
    )
    usage_after = resilient.analytics_list_by_service(
        application.threescale_client, application["service_id"], "hits", "total", usage_before + 1
    )
    assert usage_after == usage_before + 6


def test_soap_policy_nothing(api_client, application):
    "Tests if 3scale report correct usage without SOAP header"
    analytics = application.threescale_client.analytics
    usage_before = analytics.list_by_service(application["service_id"], metric_name="hits")["total"]
    api_client().get("/get")
    usage_after = resilient.analytics_list_by_service(
        application.threescale_client, application["service_id"], "hits", "total", usage_before + 1
    )
    assert usage_after == usage_before + 1
