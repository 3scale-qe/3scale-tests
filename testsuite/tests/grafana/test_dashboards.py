"""Tests for Grafana Dashboards definitions"""

import json
import pytest

DASHBOARDS = [
    ("apicast-mainapp",
     "sum(rate(nginx_http_connections{namespace='$namespace', pod=~'apicast-$env.*'}[1m])) by (state)"),
    ("apicast-services",
     "sum(rate(upstream_status"
     "{namespace='$namespace', pod=~'apicast-$env.*', service_id='$service_id'}[1m])) by (status)"),
    ("backend",
     "sum(rate(apisonator_listener_response_codes"
     "{namespace=\\\"$namespace\\\",request_type=\\\"authorize\\\"}[1m]))"),
    ("kubernetes-resources-by-namespace",
     "sum(node_namespace_pod_container:container_cpu_usage_seconds_total:sum_rate"
     "{cluster=\\\"$cluster\\\", namespace=\\\"$namespace\\\"}) by (pod)"),
    ("kubernetes-resources-by-pod",
     "sum(node_namespace_pod_container:container_cpu_usage_seconds_total:sum_rate"
     "{namespace=\\\"$namespace\\\", pod=\\\"$pod\\\", container!=\\\"POD\\\", cluster=\\\"$cluster\\\"})"
     " by (container)"),
    ("system",
     "sum(rate(rails_requests_total{namespace='$namespace',pod=~'system-app-[a-z0-9]+-[a-z0-9]+'}[1m])) by (status)"),
    ("zync",
     "sum(rate(rails_requests_total{namespace='$namespace',pod=~'zync-[a-z0-9]+-[a-z0-9]+'}[1m])) by (status)"),
]


@pytest.mark.smoke
@pytest.mark.parametrize("dashboard,expresion", DASHBOARDS)
def test_dashboards(openshift, dashboard, expresion):
    """check expresion to be inside of json definition of the dashboard"""
    client = openshift()
    ret = client.do_action('get', ['GrafanaDashboard', dashboard, '-ojson'])

    action = ret.as_dict()["actions"][0]

    if 'out_obj' in action:
        dashboard_json = action["out_obj"]["spec"]["json"]
    else:  # big objects are not parsed by default
        dashboard_json = json.loads(action['out'])["spec"]["json"]

    assert expresion in dashboard_json
