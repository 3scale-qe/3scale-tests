"""
Test Prometheus metric for content_caching.
"""
import pytest

from packaging.version import Version  # noqa # pylint: disable=unused-import
from testsuite import TESTED_VERSION, rawobj  # noqa # pylint: disable=unused-import


pytestmark = [
    pytest.mark.skipif("TESTED_VERSION < Version('2.9')"),
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-5439")]


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
    api_client.get("/anything")
    return api_client


@pytest.mark.disruptive
@pytest.mark.parametrize(("client", "apicast"), [("api_client", "3scale Apicast Staging"),
                                                 ("prod_client", "3scale Apicast Production")],
                         ids=["Staging Apicast", "Production Apicast"])
def test_content_caching(request, prometheus_client, client, apicast):
    """
    Test if cache works correctly and if prometheus contains content_caching metric.
    """
    client = request.getfixturevalue(client)

    response = client.get("/anything/test", headers=dict(origin="localhost"))
    assert response.status_code == 200
    assert response.headers.get("X-Cache-Status") != "HIT"

    response = client.get("/anything/test", headers=dict(origin="localhost"))
    assert response.status_code == 200
    assert response.headers.get("X-Cache-Status") == "HIT"

    metrics = prometheus_client.get_metrics(apicast)
    metrics = [m["metric"] for m in metrics["data"]]

    assert "content_caching" in metrics
