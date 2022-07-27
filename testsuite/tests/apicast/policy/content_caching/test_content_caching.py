"""
Test valid content caching options
"""

import time
import uuid
import pytest

from testsuite import rawobj
from testsuite.echoed_request import EchoedRequest

pytestmark = pytest.mark.require_version("2.9")


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
    return rawobj.Proxy(private_base_url("echo_api"))


@pytest.fixture(scope="module")
def client(api_client):
    """Apicast needs to load configuration in order to cache incomming requests"""
    client = api_client()
    client.get("/")
    return client


def is_hit(response):
    """Checks if request was successful and CACHE was hit"""
    return response.status_code == 200 and response.headers.get("X-Cache-Status") == "HIT"


def is_expired(response):
    """Checks if request was successful and CACHE expired"""
    return response.status_code == 200 and response.headers.get("X-Cache-Status") == "EXPIRED"


def test_caching_working_correctly(client):
    "content caching is working correctly when matchs"

    path = "/test/{0}".format(uuid.uuid4())

    assert not is_hit(client.get(path, headers=dict(origin="localhost")))

    for i in range(0, 10):
        assert is_hit(client.get(path, headers=dict(origin="localhost"))), "Request {} didn't hit the cache".format(i)


def test_caching_different_urls_with_same_subpath(client):
    "content caching is doing the right thing when path/subpaths are involved"
    assert not is_hit(client.get("/test/test", headers=dict(origin="localhost")))
    assert is_hit(client.get("/test/test", headers=dict(origin="localhost")))

    assert not is_hit(client.get("/test", headers=dict(origin="localhost")))
    assert is_hit(client.get("/test", headers=dict(origin="localhost")))


def test_caching_timeouts(client):
    "Validate caching timeouts time"

    path = "/test/{0}".format(uuid.uuid4())

    assert not is_hit(client.get(path, headers=dict(origin="localhost")))
    assert is_hit(client.get(path, headers=dict(origin="localhost")))

    # Default timeout is 60, but timers are here, so this should be safe enough
    time.sleep(70)

    assert is_expired(client.get(path, headers=dict(origin="localhost")))
    assert is_hit(client.get(path, headers=dict(origin="localhost")))


def test_caching_body_check(client):
    """Check same body response"""
    response = client.get('/test/test', headers=dict(origin="localhost"))
    assert response.status_code == 200
    assert response.headers.get("X-Cache-Status") != "HIT"
    echoed_request = EchoedRequest.create(response)

    response = client.get('/test/test', headers=dict(origin="localhost"))
    assert response.status_code == 200
    assert response.headers.get("X-Cache-Status") == "HIT"

    echoed_request_cached = EchoedRequest.create(response)
    assert echoed_request.json['uuid'] == echoed_request_cached.json['uuid']
