"""
Test for url rewriting captures policy with HTTP methods
In 2.10 version the HTTP methods were added
"""
import pytest

from packaging.version import Version  # noqa # pylint: disable=unused-import
from testsuite import rawobj, TESTED_VERSION  # noqa # pylint: disable=unused-import
from testsuite.echoed_request import EchoedRequest


pytestmark = [
    pytest.mark.skipif("TESTED_VERSION < Version('2.10')"),
    pytest.mark.issue("https://issues.jboss.org/browse/THREESCALE-6270"),
]


METHODS = ["POST", "PUT", "DELETE", "PATCH"]


@pytest.fixture(scope="module")
def policy_settings():
    """
    Set policy settings
    """
    return rawobj.PolicyConfig(
        "rewrite_url_captures",
        {
            "transformations": [
                {"match_rule": "/{var_1}/{var_2}", "template": "/{var_2}?my_arg={var_1}", "methods": ["GET"]}
            ]
        },
    )


@pytest.fixture(scope="module")
def service(service):
    """
    Add POST, PUT, DELETE, PATCH mapping rules so we can make successful requests
    """
    metric = service.metrics.create(rawobj.Metric("metric"))
    for method in METHODS:
        service.proxy.list().mapping_rules.create(rawobj.Mapping(metric, "/", method))
    service.proxy.deploy()

    return service


@pytest.fixture(scope="module")
def api_client(api_client):
    """Ensure all is up & running by get request as the other requests in tests are not retried"""
    api_client().get("/get")
    return api_client


def test_rewrite_url_captures(api_client):
    """it will rewrite /hello/get to /get?my_arg=hello"""
    response = api_client().get("/hello/get")
    assert response.status_code == 200

    echoed_request = EchoedRequest.create(response)
    assert echoed_request.params["my_arg"] == "hello"
    assert echoed_request.path == "/get"


@pytest.mark.parametrize("method", METHODS)
def test_wont_rewrite(api_client, method):
    """It will not rewrite url of request with other HTTP methods"""
    response = api_client().request(method, f"/anything/{method}")
    assert response.status_code == 200

    echoed_request = EchoedRequest.create(response)
    assert echoed_request.path == f"/anything/{method}"
    assert "my_arg" not in echoed_request.params
