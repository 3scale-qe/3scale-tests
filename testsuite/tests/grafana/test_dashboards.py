"""Tests for Grafana Dashboards definitions"""
import pytest
from packaging.version import Version  # noqa # pylint: disable=unused-import

from testsuite import TESTED_VERSION  # noqa # pylint: disable=unused-import
from testsuite.capabilities import Capability

pytestmark = [
    pytest.mark.skipif("TESTED_VERSION < Version('2.9')"),
    pytest.mark.required_capabilities(Capability.OCP4),
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-7961")
]

DASHBOARDS = [
    ("apicast-mainapp",
     "sum(rate(nginx_http_connections{namespace='$namespace', pod=~'apicast-$env.*'}[1m])) by (state)"),
    ("apicast-services",
     "sum(rate(upstream_status{namespace='$namespace', pod=~'apicast-$env.*', service_id='$service_id'}[1m]))"
     " by (status)"),
    ("backend",
     'sum(rate(apisonator_listener_response_codes{namespace=\\"$namespace\\",request_type=\\"authorize\\"}[1m]))'),
    pytest.param("kubernetes-resources-by-namespace",
                 'sum(node_namespace_pod_container:container_cpu_usage_seconds_total:sum_rate'
                 '{cluster=\\"$cluster\\", namespace=\\"$namespace\\"}) by (pod)',
                 marks=pytest.mark.skipif(TESTED_VERSION >= Version('2.13'),
                                          reason="This Dashboard is not applicable to this 3scale version")),
    pytest.param("kubernetes-resources-by-namespace",
                 'sum(node_namespace_pod_container:container_cpu_usage_seconds_total:sum_irate'
                 '{cluster=\\"$cluster\\", namespace=\\"$namespace\\"}) by (pod)',
                 marks=pytest.mark.skipif(TESTED_VERSION < Version('2.13'),
                                          reason="This Dashboard is not applicable to this 3scale version")),
    pytest.param("kubernetes-resources-by-pod",
                 'sum(node_namespace_pod_container:container_cpu_usage_seconds_total:sum_rate'
                 '{namespace=\\"$namespace\\", pod=\\"$pod\\", container!=\\"POD\\", cluster=\\"$cluster\\"})'
                 ' by (container)',
                 marks=pytest.mark.skipif(TESTED_VERSION >= Version('2.13'),
                                          reason="This Dashboard is not applicable to this 3scale version")),
    pytest.param("kubernetes-resources-by-pod",
                 'sum(node_namespace_pod_container:container_cpu_usage_seconds_total:sum_irate'
                 '{namespace=\\"$namespace\\", pod=\\"$pod\\", container!=\\"POD\\", cluster=\\"$cluster\\"})'
                 ' by (container)',
                 marks=pytest.mark.skipif(TESTED_VERSION < Version('2.13'),
                                          reason="This Dashboard is not applicable to this 3scale version")),
    ("system",
     "sum(rate(rails_requests_total{namespace='$namespace',pod=~'system-app-[a-z0-9]+-[a-z0-9]+'}[1m])) by (status)"),
    ("zync",
     "sum(rate(rails_requests_total{namespace='$namespace',pod=~'zync-[a-z0-9]+-[a-z0-9]+'}[1m])) by (status)"),
]


@pytest.mark.parametrize("dashboard_name,expression", DASHBOARDS)
def test_dashboard(openshift, dashboard_name, expression):
    """check expression to be inside json definition of the dashboard"""
    dashboard = openshift().do_action('get', ['GrafanaDashboard', dashboard_name, '-ojson'], parse_output=True)

    assert expression in dashboard.model.spec.json
