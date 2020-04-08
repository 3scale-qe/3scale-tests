"""
Rewritten /spec/functional_specs/hit_limit_spec.rb
Rewritten /spec/functional_specs/hit_limit_with_retry_after_spec.rb

When having application with an application plan, that has limit on number
of hits per minute, the requests are accepted until the limit is reached.
Further requests in the same minute are denied.
When the next minute comes, the requests are again accepted.

When the request is denied the headers should contain the
'retry-after' header.
After waiting for the time in the 'retry-after' header, the request should
be accepted.
"""

import datetime
import time
import pytest
from testsuite import rawobj
from testsuite.utils import blame


@pytest.fixture(scope="module")
def application_silver(application, custom_app_plan, custom_application, request):
    """
    Creates application with an application plan, that limits the number of
    requests in a minute to ten
    """
    service = application.service
    metric = service.metrics.list()[0]

    proxy = service.proxy.list()

    plan_silver = custom_app_plan(
        rawobj.ApplicationPlan(blame(request, "silver")), service)
    plan_silver.limits(metric).create({
        "metric_id": metric["id"], "period": "minute", "value": 10})

    application = custom_application(
        rawobj.Application(blame(request, "silver_app"), plan_silver))

    proxy.update()

    return application


@pytest.fixture(scope="module")
def application_gold(application, custom_app_plan, custom_application, request):
    """
    Creates the application with an app plan that does not limits the number
    of requests
    """
    service = application.service

    proxy = service.proxy.list()

    plan_gold = custom_app_plan(rawobj.ApplicationPlan(blame(request, "gold")), service)
    application = custom_application(rawobj.Application(blame(request, "gold_app"), plan_gold))

    proxy.update()

    return application


@pytest.fixture(scope="module")
def silver_client(application_silver):
    """
    returns api client for silver application
    """
    return application_silver.api_client()


@pytest.fixture(scope="module")
def gold_client(application_gold):
    """
    returns api client for silver application
    """
    return application_gold.api_client()


def wait_interval(min_sec=15, max_sec=45):
    """
    The requests has to be send between the 15th and 45th second of the minute
    When the time is outside of this interval, waits until the start of a next one
    """
    seconds = datetime.datetime.now().second
    if seconds < min_sec or seconds > max_sec:
        sleep_time = (60 - seconds + min_sec) % 60
        time.sleep(sleep_time)


def wait_until_next_minute(min_sec=15, max_sec=45):
    """
     Waits until the start of the next minute when are the limits reseted,
     then waits until the start of the interval allowed to sent requests
    """
    seconds = datetime.datetime.now().second
    time.sleep(60 - seconds)
    if min_sec < seconds < max_sec:
        wait_interval()


def assert_limit_works(client, limit):
    """
    Assert that limit + 1 requests send via the client are accepted,
    the next should be denied
    """
    for i in range(limit + 1):
        response = client.get("/")
        assert response.status_code == 200, f"Response of the request " \
                                            f"number {i} should be 200"
        # wait for 0.125 as the original ruby tests waits after making request
        time.sleep(0.125)

    for i in range(2):
        response = client.get("/")
        assert response.status_code == 429, f"Response of the request {limit + 1 + i} " \
                                            f"should be 429"
        # wait for 0.125 as the original ruby tests waits after making request
        time.sleep(0.125)


def test_limit_exceeded(silver_client, gold_client):
    """
    Unlimited number of requests sent via the gold app should be accepted and return 200
    Eleven requests via silver app should be accepted, the next one should be denied
    In the next minute, the eleven requests should be again accepted, further ones
    denied
    """
    for i in range(15):
        assert gold_client.get("/").status_code == 200, f"Response of the request " \
                                                        f"number {i} should be 200"
        # wait for 0.125 as the original ruby tests waits after making request
        time.sleep(0.125)

    wait_interval()

    assert_limit_works(silver_client, limit=10)

    wait_until_next_minute()

    assert_limit_works(silver_client, limit=10)


def wait_until_retry_after(response):
    """
    Waits for the time from the 'retry-after' header of the response
    """
    retry_after = response.headers["retry-after"]
    time.sleep(int(retry_after))


def test_retry_after(silver_client):
    """
    The response for denied request should contain the 'retry-after' header
    After waiting the time from the 'retry-after' header, the following requests
    should be again accepted
    """
    response = silver_client.get("/")
    while response.status_code != 429:
        # wait for 0.125 as the original ruby tests waits after making request
        time.sleep(0.125)
        response = silver_client.get("/")

    assert "retry-after" in response.headers

    wait_until_retry_after(response)

    assert_limit_works(silver_client, limit=10)
