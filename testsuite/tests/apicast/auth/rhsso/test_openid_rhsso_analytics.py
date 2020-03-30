"""
Rewrite of the spec/functional_specs/auth/rhsso/openid_rhsso_analytics_spec.rb
"""


def test_rhsso_analytics(application, api_client):
    """Test checks if the oidc requests are counted to the analytics"""
    analytics = application.threescale_client.analytics
    usage_before = analytics.list_by_service(application["service_id"], metric_name="hits")["total"]

    for _ in range(5):
        api_client.get("/get")

    usage_after = analytics.list_by_service(application["service_id"], metric_name="hits")["total"]
    assert usage_after == usage_before + 5
