"""
Test Prometheus metric for content_caching.
"""
import time

import pytest

from packaging.version import Version  # noqa # pylint: disable=unused-import
from testsuite import TESTED_VERSION, rawobj  # noqa # pylint: disable=unused-import
from testsuite.prometheus import PROMETHEUS_REFRESH

pytestmark = [
    pytest.mark.skipif("TESTED_VERSION < Version('2.9')"),
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-5439"),
    ]


@pytest.fixture(scope="module")
def service(service):
    """Configurate content_caching policy"""
    service.proxy.list().policies.append(rawobj.PolicyConfig("content_caching", {
        "rules": [{
            "cache": True,
            "header": "X-Cache-Status",
            "condition": {
                "combine_op": "and",
                "operations": [{
                    "left": "oo",
                    "op": "==",
                    "right": "oo"
                }]
            }
        }]
    }))
    service.proxy.deploy()
    return service


@pytest.mark.disruptive
@pytest.mark.parametrize(("client", "apicast"), [("api_client", "apicast-staging"),
                                                 ("prod_client", "apicast-production")
                                                 ],
                         ids=["Staging Apicast", "Production Apicast"])
def test_content_caching(request, prometheus, client, apicast):
    """
    Test if cache works correctly and if prometheus contains content_caching metric.
    """
    client = request.getfixturevalue(client)
    client = client()
    counts_before = extract_caching(prometheus, "content_caching", apicast)

    response = client.get("/anything/test", headers=dict(origin="localhost"))
    assert response.status_code == 200
    assert response.headers.get("X-Cache-Status") != "HIT"

    response = client.get("/anything/test", headers=dict(origin="localhost"))
    assert response.status_code == 200
    assert response.headers.get("X-Cache-Status") == "HIT"

    # prometheus is downloading metrics periodicity, we need to wait for next fetch
    time.sleep(PROMETHEUS_REFRESH)

    metrics = prometheus.get_metrics(apicast)
    assert "content_caching" in metrics

    counts_after = extract_caching(prometheus, "content_caching", apicast)

    assert int(counts_after['HIT']) == int(counts_before['HIT']) + 1


def extract_caching(prometheus, query, apicast):
    """
    Given a prometheus query, returns dict with response
    codes and counts associated with the response code
    """
    metric_response_codes = prometheus.get_metric(query)
    key_value_map = {'EXPIRED': 0, 'HIT': 0, 'MISS': 0}
    for response_code_metric in metric_response_codes:
        if apicast != response_code_metric['metric']['container']:
            continue

        key_value_map[response_code_metric['metric']['status']] \
            = response_code_metric['value'][1]
    return key_value_map
