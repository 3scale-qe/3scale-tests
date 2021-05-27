"""
Test Prometheus metric for content_caching.
"""
import time

import pytest

from packaging.version import Version  # noqa # pylint: disable=unused-import
from testsuite import TESTED_VERSION, rawobj  # noqa # pylint: disable=unused-import

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


@pytest.fixture(scope="module")
def prod_client(prod_client):
    """Hit production apicast so that we can have metrics from it and that we can cache incoming requests"""
    client = prod_client()
    assert client.get("/anything").status_code == 200
    return client


@pytest.fixture(scope="module")
def api_client(api_client):
    """Apicast needs to load configuration in order to cache incoming requests"""
    client = api_client()
    client.get("/anything")
    return client


@pytest.mark.disruptive
@pytest.mark.parametrize(("client", "apicast"), [("api_client", "3scale Apicast Staging"),
                                                 ("prod_client", "3scale Apicast Production")
                                                 ],
                         ids=["Staging Apicast", "Production Apicast"])
def test_content_caching(request, prometheus, client, apicast):
    """
    Test if cache works correctly and if prometheus contains content_caching metric.
    """
    client = request.getfixturevalue(client)
    counts_before = extract_caching(prometheus, "content_caching", apicast)

    response = client.get("/anything/test", headers=dict(origin="localhost"))
    assert response.status_code == 200
    assert response.headers.get("X-Cache-Status") != "HIT"

    response = client.get("/anything/test", headers=dict(origin="localhost"))
    assert response.status_code == 200
    assert response.headers.get("X-Cache-Status") == "HIT"

    # prometheus is downloading this metrics each 5 seconds, we need to wait
    time.sleep(10)

    metrics = prometheus.get_metrics(apicast)
    metrics = [m["metric"] for m in metrics["data"]]
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
        if apicast != response_code_metric['metric']['job']:
            continue

        key_value_map[response_code_metric['metric']['status']] \
            = response_code_metric['value'][1]
    return key_value_map
