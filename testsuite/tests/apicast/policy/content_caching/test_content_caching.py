"""
Test valid content caching options
"""

import time
import uuid
from packaging.version import Version  # noqa # pylint: disable=unused-import
import pytest

from testsuite import rawobj, TESTED_VERSION  # noqa # pylint: disable=unused-import
from testsuite.echoed_request import EchoedRequest

pytestmark = pytest.mark.skipif("TESTED_VERSION < Version('2.9')")


@pytest.fixture(scope="module")
def policy_settings():
    "config of cors policy"
    return rawobj.PolicyConfig("content_caching", {
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
    })


@pytest.fixture(scope="module")
def service_proxy_settings(private_base_url):
    "content caching endpoint to be used"
    return rawobj.Proxy(private_base_url("echo-api"))


@pytest.fixture(scope="module")
def api_client(api_client):
    """Apicast needs to load configuration in order to cache incomming requests"""
    api_client.get("/")
    return api_client


def test_caching_working_correctly(api_client):
    "content caching is working correctly when matchs"

    path = "/test/{0}".format(uuid.uuid4())
    request = lambda: api_client.get(path, headers=dict(origin="localhost"))  # noqa: E731
    is_hit = lambda response: response.headers.get("X-Cache-Status") == "HIT"  # noqa: E731

    assert not is_hit(request())

    for i in range(0, 10):
        assert is_hit(request()), "Request {} didn't hit the cache".format(i)


def test_caching_different_urls_with_same_subpath(api_client):
    "content caching is doing the right thing when path/subpaths are involved"

    request = lambda path: api_client.get(path, headers=dict(origin="localhost"))  # noqa: E731
    is_hit = lambda response: response.headers.get("X-Cache-Status") == "HIT"  # noqa: E731

    assert not is_hit(request("/test/test/"))
    assert is_hit(request("/test/test/"))

    assert not is_hit(request("/test/"))
    assert is_hit(request("/test/"))


def test_caching_timeouts(api_client):
    "Validate caching timeouts time"

    path = "/test/{0}".format(uuid.uuid4())

    request = lambda: api_client.get(path, headers=dict(origin="localhost"))  # noqa: E731
    is_hit = lambda response: response.headers.get("X-Cache-Status") == "HIT"  # noqa: E731
    is_expired = lambda response: response.headers.get("X-Cache-Status") == "EXPIRED"  # noqa: E731

    assert not is_hit(request())
    assert is_hit(request())

    # Default timeout is 60, but timers are here, so this should be safe enough
    time.sleep(70)

    assert is_expired(request())
    assert is_hit(request())


def test_caching_body_check(api_client):
    """Check same body response"""
    response = api_client.get('/test/test', headers=dict(origin="localhost"))
    echoed_request = EchoedRequest.create(response)

    assert response.status_code == 200
    assert response.headers.get("X-Cache-Status") != "HIT"

    response = api_client.get('/test/test', headers=dict(origin="localhost"))
    echoed_request_cached = EchoedRequest.create(response)

    assert response.status_code == 200
    assert response.headers.get("X-Cache-Status") == "HIT"
    assert echoed_request.json['uuid'] == echoed_request_cached.json['uuid']
