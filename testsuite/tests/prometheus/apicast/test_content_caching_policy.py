"""
Test Prometheus metric for content_caching.
"""

import backoff
import pytest

from packaging.version import Version  # noqa # pylint: disable=unused-import
from testsuite import TESTED_VERSION, rawobj  # noqa # pylint: disable=unused-import
from testsuite.prometheus import get_metrics_keys

pytestmark = [
    pytest.mark.skipif("TESTED_VERSION < Version('2.9')"),
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-5439"),
]


@pytest.fixture(scope="module")
def service(service):
    """Configurate content_caching policy"""
    service.proxy.list().policies.append(
        rawobj.PolicyConfig(
            "content_caching",
            {
                "rules": [
                    {
                        "cache": True,
                        "header": "X-Cache-Status",
                        "condition": {"combine_op": "and", "operations": [{"left": "oo", "op": "==", "right": "oo"}]},
                    }
                ]
            },
        )
    )
    service.proxy.deploy()
    return service


@pytest.mark.disruptive
@pytest.mark.parametrize(
    ("client", "apicast"),
    [("api_client", "apicast-staging"), ("prod_client", "apicast-production")],
    ids=["Staging Apicast", "Production Apicast"],
)
def test_content_caching(request, prometheus, client, apicast):
    """
    Test if cache works correctly and if prometheus contains content_caching metric.
    """
    origin_localhost = {"origin": "localhost"}
    client = request.getfixturevalue(client)()
    # """Hit apicast so that we can have metrics from it and that we can cache incoming requests"""
    # """Apicast needs to load configuration in order to cache incoming requests"""
    response = client.get("/get", headers=origin_localhost)
    assert response.status_code == 200
    assert response.headers.get("X-Cache-Status") != "HIT"

    @backoff.on_predicate(backoff.fibo, lambda x: not x, max_tries=10, jitter=None)
    def wait():
        """Wait until content_caching key is in prometheus"""
        prometheus.wait_on_next_scrape(apicast)
        metrics = get_metrics_keys(prometheus.get_metrics(labels={"container": apicast}))
        return "content_caching" in metrics

    wait()

    counts_before = extract_caching(prometheus, "content_caching", apicast)

    response = client.get("/anything/test", headers=origin_localhost)
    assert response.status_code == 200
    assert response.headers.get("X-Cache-Status") != "HIT"

    response = client.get("/anything/test", headers=origin_localhost)
    assert response.status_code == 200
    assert response.headers.get("X-Cache-Status") == "HIT"

    # prometheus is downloading metrics periodicity, we need to wait for next fetch
    prometheus.wait_on_next_scrape(apicast)

    metrics = get_metrics_keys(prometheus.get_metrics(labels={"container": apicast}))
    assert "content_caching" in metrics

    counts_after = extract_caching(prometheus, "content_caching", apicast)

    assert int(counts_after["HIT"]) == int(counts_before["HIT"]) + 1


def extract_caching(prometheus, query, apicast):
    """
    Given a prometheus query, returns dict with response
    codes and counts associated with the response code
    """
    metric_response_codes = prometheus.get_metrics(query, {"container": apicast})
    key_value_map = {"EXPIRED": 0, "HIT": 0, "MISS": 0}
    for response_code_metric in metric_response_codes:
        key_value_map[response_code_metric["metric"]["status"]] = response_code_metric["value"][1]
    return key_value_map
