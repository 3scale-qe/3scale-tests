"""
Rewrite: /spec/functional_specs/analytics_spec.rb

When getting analytics for the number of hits to the service, the number is
equal to the sum of the number of requests made by all applications

When getting analytics for individual applications, the number is equal to
the number of requests send by the application.
"""
import pytest
from testsuite import rawobj
from testsuite import resilient
from testsuite.utils import blame

pytestmark = pytest.mark.required_capabilities()


@pytest.fixture(scope="module")
def app2(service, custom_application, custom_app_plan, request, lifecycle_hooks):
    """Creates a second application"""
    plan = custom_app_plan(rawobj.ApplicationPlan(blame(request, "aplan")), service)
    return custom_application(rawobj.Application(blame(request, "app2"), plan), hooks=lifecycle_hooks)


def test_hits_service(application, api_client, app2):
    """
    Send requests using the first application
    Send requests using the second application

    If the requests were successful, assert that:
    - The number of hits to the service is equal to the sum of the number of requests
    - The number of hits to each app is equal to the number of requests made
      through that app
    """
    analytics = app2.threescale_client.analytics
    prev_service_hits = analytics.list_by_service(app2["service_id"], metric_name="hits")["total"]
    prev_app_hits = analytics.list_by_application(application, metric_name="hits")["total"]
    prev_app2_hits = analytics.list_by_application(app2, metric_name="hits")["total"]
    requests_app = 6
    requests_app2 = 4

    client = api_client()
    client2 = api_client(app2)

    for _ in range(requests_app):
        assert client.get("/get").status_code == 200

    for _ in range(requests_app2):
        assert client2.get("/get").status_code == 200

    metrics_service = resilient.analytics_list_by_service(
        app2.threescale_client, app2["service_id"], "hits", "total", requests_app + requests_app2
    )
    assert metrics_service == prev_service_hits + requests_app + requests_app2

    metrics_app = analytics.list_by_application(application, metric_name="hits")["total"]
    assert metrics_app == prev_app_hits + requests_app

    metrics_app2 = analytics.list_by_application(app2, metric_name="hits")["total"]
    assert metrics_app2 == prev_app2_hits + requests_app2
