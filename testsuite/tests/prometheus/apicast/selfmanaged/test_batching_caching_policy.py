"""
Test Prometheus metric for content_caching.
"""
from datetime import datetime, timedelta
import pytest

from packaging.version import Version  # noqa # pylint: disable=unused-import
from testsuite import TESTED_VERSION, rawobj  # noqa # pylint: disable=unused-import
from testsuite.capabilities import Capability

pytestmark = [
    pytest.mark.skipif("TESTED_VERSION < Version('2.9')"),
    pytest.mark.required_capabilities(Capability.OCP4),
    ]

BATCH_REPORT_SECONDS = 50
NUM_OF_REQUESTS = 5


@pytest.fixture(scope="module")
def service(service):
    """Adds policies to servies"""
    service.proxy.list().policies.append(
        rawobj.PolicyConfig("3scale_batcher", {"batch_report_seconds": BATCH_REPORT_SECONDS}))
    return service


@pytest.fixture(scope="module")
def pod_monitor(prometheus, openshift, staging_gateway):
    """ define pod monitor for prometheus """

    apicast_openshift_client = staging_gateway.openshift
    apicast_deployment = staging_gateway.deployment
    apicast_operator_namespace = apicast_openshift_client.project_name

    openshift_client = openshift()
    namespace = openshift_client.project_name

    apicast_obj = openshift_client.create(f"""apiVersion: monitoring.coreos.com/v1
kind: PodMonitor
metadata:
  name: apicast-selfmanaged-{apicast_deployment}
  namespace: {namespace}
  labels:
    app: 3scale-api-management
    threescale_component: apicast
    threescale_component_element: staging
spec:
  namespaceSelector:
    matchNames:
    - {apicast_operator_namespace}
  podMetricsEndpoints:
    - path: /metrics
      port: metrics
      scheme: http
  selector:
    matchLabels:
      deployment: {apicast_deployment}
        """)

    prometheus.wait_on_next_scrape(apicast_deployment, datetime.utcnow() + timedelta(seconds=60))

    yield

    apicast_obj.delete()


# pylint: disable=unused-argument
def test_batcher_policy(prometheus, pod_monitor, api_client, staging_gateway, application):
    """Test if return correct number of usages of a service in batch"""
    client = api_client()

    apicast_deployment = staging_gateway.deployment

    metrics_keys = prometheus.get_metrics(apicast_deployment)

    assert "batching_policy_auths_cache_hits" not in metrics_keys
    assert "batching_policy_auths_cache_misses" not in metrics_keys

    for _ in range(NUM_OF_REQUESTS):
        client.get("/get")

    prometheus.wait_on_next_scrape(apicast_deployment, datetime.utcnow() + timedelta(seconds=BATCH_REPORT_SECONDS))
    metrics_keys = prometheus.get_metrics(apicast_deployment)

    assert "batching_policy_auths_cache_hits" in metrics_keys
    assert "batching_policy_auths_cache_misses" in metrics_keys

    hits, misses = get_batching_metrics(prometheus, apicast_deployment)

    assert int(hits) == NUM_OF_REQUESTS - 1
    assert int(misses) == 1


def get_batching_metrics(prometheus, apicast_deployment):
    """ extract hits and misses count from prometheus """
    hits_metrics = prometheus.get_metric("batching_policy_auths_cache_hits")
    misses_metrics = prometheus.get_metric("batching_policy_auths_cache_misses")

    hits = [m for m in hits_metrics if m['metric']['container'] == apicast_deployment][0]['value'][1]
    misses = [m for m in misses_metrics if m['metric']['container'] == apicast_deployment][0]['value'][1]

    return hits, misses
