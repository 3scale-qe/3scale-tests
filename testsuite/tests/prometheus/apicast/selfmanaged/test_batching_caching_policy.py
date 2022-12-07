"""
Test Prometheus metric for content_caching.
"""
from datetime import datetime, timedelta
import pytest

from packaging.version import Version  # noqa # pylint: disable=unused-import
from testsuite import APICAST_OPERATOR_VERSION, rawobj  # noqa # pylint: disable=unused-import
from testsuite.capabilities import Capability
from testsuite.prometheus import get_metrics_keys

pytestmark = [
    pytest.mark.nopersistence,
    pytest.mark.skipif("APICAST_OPERATOR_VERSION < Version('0.5.2')"),
    pytest.mark.required_capabilities(Capability.OCP4, Capability.APICAST),
    ]

BATCH_REPORT_SECONDS = 50
NUM_OF_REQUESTS = 5


@pytest.fixture(scope="module")
def service(service):
    """Adds policies to servies"""
    service.proxy.list().policies.append(
        rawobj.PolicyConfig("3scale_batcher", {"batch_report_seconds": BATCH_REPORT_SECONDS}))
    return service


def pod_monitor_object_definition(apicast_deployment, namespace, apicast_operator_namespace=""):
    """Return PodMonitor yaml definition"""
    selector_text = ""
    if apicast_operator_namespace:
        selector_text = ("  namespaceSelector:\n"
                         "    matchNames:\n"
                         f"    - {apicast_operator_namespace}\n")

    return f"""apiVersion: monitoring.coreos.com/v1
kind: PodMonitor
metadata:
  name: apicast-selfmanaged-{apicast_deployment}
  namespace: {namespace}
  labels:
    app: 3scale-api-management
    threescale_component: apicast
    threescale_component_element: staging
spec:
{selector_text}
  podMetricsEndpoints:
    - path: /metrics
      port: metrics
      scheme: http
  selector:
    matchLabels:
      deployment: {apicast_deployment}
"""


@pytest.fixture(scope="module")
def pod_monitor(prometheus, openshift, staging_gateway):
    """ define pod monitor for prometheus """

    apicast_openshift_client = staging_gateway.openshift
    apicast_deployment = staging_gateway.deployment.name
    apicast_operator_namespace = apicast_openshift_client.project_name

    openshift_client = openshift()
    namespace = openshift_client.project_name

    #  object in 3scale namespace (for prometheus deployed by free-deployer)
    pod_monitor_3scale_namespace = openshift_client.create(
        pod_monitor_object_definition(apicast_deployment, namespace, apicast_operator_namespace))

    #  object in apicast operator namespace (for openshift user workload monitoring)
    pod_monitor_apicast_namespace = openshift_client.create(
        pod_monitor_object_definition(apicast_deployment, apicast_operator_namespace))

    #  wait a little more so operator will get this config and have time to do a first scrape
    prometheus.wait_on_next_scrape(apicast_deployment, datetime.utcnow() + timedelta(seconds=60))

    yield

    pod_monitor_3scale_namespace.delete()
    pod_monitor_apicast_namespace.delete()


# pylint: disable=unused-argument
def test_batcher_policy(prometheus, pod_monitor, api_client, staging_gateway, application):
    """Test if return correct number of usages of a service in batch"""
    client = api_client()

    apicast_deployment = staging_gateway.deployment.name
    labels = {"namespace": staging_gateway.openshift.project_name, "container": apicast_deployment}

    prometheus.wait_on_next_scrape(apicast_deployment)

    metrics_keys = get_metrics_keys(prometheus.get_metrics(labels=labels))

    assert "batching_policy_auths_cache_hits" not in metrics_keys
    assert "batching_policy_auths_cache_misses" not in metrics_keys

    for _ in range(NUM_OF_REQUESTS):
        client.get("/get")

    prometheus.wait_on_next_scrape(apicast_deployment, datetime.utcnow() + timedelta(seconds=BATCH_REPORT_SECONDS))
    metrics_keys = get_metrics_keys(prometheus.get_metrics(labels=labels))

    assert "batching_policy_auths_cache_hits" in metrics_keys
    assert "batching_policy_auths_cache_misses" in metrics_keys

    hits, misses = get_batching_metrics(prometheus, apicast_deployment, staging_gateway.openshift.project_name)

    assert (int(hits), int(misses)) == (NUM_OF_REQUESTS-1, 1)


def get_batching_metrics(prometheus, apicast_deployment, namespace):
    """ extract hits and misses count from prometheus """
    hits_metrics = prometheus.get_metrics("batching_policy_auths_cache_hits",
                                          {"namespace": namespace, "container": apicast_deployment})
    misses_metrics = prometheus.get_metrics("batching_policy_auths_cache_misses",
                                            {"namespace": namespace, "container": apicast_deployment})

    hits = hits_metrics[0]['value'][1]
    misses = misses_metrics[0]['value'][1]

    return hits, misses
