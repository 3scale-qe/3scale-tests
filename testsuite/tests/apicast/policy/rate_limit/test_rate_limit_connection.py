# pylint: disable=line-too-long

"""
Test whether rate_limit connection controls number of simultaneous incoming
connections

Rewrite:
    spec/functional_specs/policies/rate_limit/connection/liquid/rate_limit_connection_liquid_key_name_spec.rb
    spec/functional_specs/policies/rate_limit/connection/liquid/rate_limit_connection_liquid_service_false_spec.rb
    spec/functional_specs/policies/rate_limit/connection/liquid/rate_limit_connection_liquid_service_true_spec.rb
    spec/functional_specs/policies/rate_limit/connection/liquid/rate_limit_connection_matches_false_spec.rb
    spec/functional_specs/policies/rate_limit/connection/liquid/rate_limit_connection_matches_true_spec.rb
    spec/functional_specs/policies/rate_limit/connection/plain_text/false_condition/rate_limit_multiple_connection_global_false_spec.rb
    spec/functional_specs/policies/rate_limit/connection/plain_text/false_condition/rate_limit_multiple_connection_service_false_spec.rb
    spec/functional_specs/policies/rate_limit/connection/plain_text/false_condition/rate_limit_multiple_prepend_connection_global_false_spec.rb
    spec/functional_specs/policies/rate_limit/connection/plain_text/true_condition/rate_limit_multiple_connection_global_true_spec.rb
    spec/functional_specs/policies/rate_limit/connection/plain_text/true_condition/rate_limit_multiple_connection_service_true_spec.rb
    spec/functional_specs/policies/rate_limit/connection/plain_text/true_condition/rate_limit_multiple_prepend_connection_global_true_spec.rb

Actually this is 'scratched'. Does 'plain-to-plain' comparison make sense?
    spec/functional_specs/policies/rate_limit/connection/plain_text/false_condition/rate_limit_connection_global_false_spec.rb
    spec/functional_specs/policies/rate_limit/connection/plain_text/false_condition/rate_limit_connection_service_false_spec.rb
    spec/functional_specs/policies/rate_limit/connection/plain_text/true_condition/rate_limit_connection_global_true_spec.rb
    spec/functional_specs/policies/rate_limit/connection/plain_text/true_condition/rate_limit_connection_service_true_spec.rb
"""

from datetime import datetime, timedelta, timezone
from pprint import pformat
import asyncio
import random

import httpx
import pytest

from testsuite import rawobj
from testsuite.httpx import AsyncClientHook
from testsuite.utils import randomize, blame

# the results can be bit unstable due to higher load caused by parallel
# http requests
pytestmark = pytest.mark.flaky

TOTAL_REQUESTS = 20
CONNECTIONS = 10
BURST = 5
DELAY = 9
DATEFMT = "%a, %d %b %Y %H:%M:%S GMT"
WAIT = 15


@pytest.mark.asyncio
async def test_rate_limit_connection_no_limit(logger, client, client2):
    """The call not matching the condition won't be limited"""

    responses = await concurrent_requests(logger, client, client2, limit_me="no")

    # total responses
    assert len(responses) == TOTAL_REQUESTS

    # all responses should be ok
    assert all(i.status_code == 200 for i in responses)


@pytest.mark.asyncio
async def test_rate_limit_connection_u(logger, client, client2):
    """
    The call matching the condition will be limited to CONNECTIONS simultaneous
    connections and additional burst of BURST will be DELAY delayed, rest will
    receive 429.
    """

    responses = await concurrent_requests(logger, client, client2, limit_me="yes")

    # total responses
    assert len(responses) == TOTAL_REQUESTS

    # responses should be ok (connections limit + burst)
    assert len([i for i in responses if i.status_code == 200]) == CONNECTIONS + BURST

    # responses should receive 429 (above limit & burst)
    assert len([i for i in responses if i.status_code == 429]) == TOTAL_REQUESTS - (CONNECTIONS + BURST)

    # ok responses should be finished DELAY seconds later (delayed burst)
    delay = timedelta(seconds=DELAY)
    times = sorted([datetime.strptime(i.headers["Date"], DATEFMT) for i in responses if i.status_code == 200])
    first = times[0]
    assert len([i for i in times if i - first < delay]) == CONNECTIONS
    assert len([i for i in times if i - first >= delay]) == BURST


async def concurrent_requests(logger, client1, client2, limit_me):
    """Make simultaneous requests

    Args:
        :param logger: logger to use for logging
        :param client1: a client to use to make requests
        :param client2: a client of other application to use to make requests
        :param limit_me: a value for 'X-Limit-Me' header used to distinguish
            whether to apply rate_limit or not, two expected values: 'yes' or 'no'

    :returns: collection of responses from concurrent requests"""

    range1 = TOTAL_REQUESTS
    range2 = 0
    if client2 is not None:
        range1 = TOTAL_REQUESTS // 2
        range2 = TOTAL_REQUESTS - range1

    futures = [get(client1, limit_me, f"/delay/{WAIT}") for _ in range(range1)]
    futures += [get(client2, limit_me, f"/delay/{WAIT}") for _ in range(range2)]
    responses = await asyncio.gather(*futures)

    strptime = datetime.strptime
    # a tuple (status_code, request Date header, response Date header) for
    # each request will be logged
    report = [
        (i.status_code, strptime(i.request.headers["Date"], DATEFMT), strptime(i.headers["Date"], DATEFMT))
        for i in responses
    ]

    # it will be sorted by response Date header
    report.sort(key=lambda k: k[2])

    logger.info("Request/Response Date headers:\n" + pformat(report))

    return responses


async def get(client, limit_me, relpath):
    """Helper to make async request with correct Date header"""
    # let's spread requests over short period; avoid all at one moment
    await asyncio.sleep(random.uniform(0, WAIT - DELAY - 2))

    return await client.get(
        relpath, headers={"X-Limit-Me": limit_me, "Date": datetime.now(timezone.utc).strftime(DATEFMT)}
    )


@pytest.fixture
def policy_settings(variation, key_scope, matching_rule, redis_url, logger):
    """Configure rate_limit policy

    Set connection_limiters to allow CONNECTIONS connections and burst of BURST
    to be delayed for DELAY seconds.
    Set a condition to match header 'X-Limit-Me' according to eq/RE rule Keep
    single or append/prepend another connection_limiter with 500 conn limit"""

    # variation == "single"  # have one single connection limiter
    rate_limit = rawobj.PolicyConfig(
        "rate_limit", {"connection_limiters": [connection_limiter(key_scope, matching_rule)]}
    )

    if variation == "double":  # have two connection limiters (doubled)
        rate_limit = rawobj.PolicyConfig(
            "rate_limit",
            {
                "connection_limiters": [
                    connection_limiter(key_scope, matching_rule, "{{ remote_addr }}, 500)"),
                    connection_limiter(key_scope, matching_rule),
                ]
            },
        )
    elif variation == "rev-order":  # have two connection limiters in opposite order
        rate_limit = rawobj.PolicyConfig(
            "rate_limit",
            {
                "connection_limiters": [
                    connection_limiter(key_scope, matching_rule),
                    connection_limiter(key_scope, matching_rule, "{{ remote_addr }}, 500)"),
                ]
            },
        )

    if key_scope == "global":
        rate_limit["configuration"]["redis_url"] = redis_url("global")

    logger.info("rate_limit policy:\n" + pformat(rate_limit))

    return rate_limit


def connection_limiter(key_scope, matching_rule, key_name="{{ host }}", conn=CONNECTIONS):
    """helper to create connection_limiter of rate_limit policy configuration"""

    return {
        "key": {"name": randomize(key_name), "name_type": "liquid", "scope": key_scope},
        "condition": {
            "combine_op": "and",
            "operations": [
                {
                    "left_type": "liquid",
                    "left": "{{ headers['X-Limit-Me'] }}",
                    "op": matching_rule[0],
                    "right_type": "plain",
                    "right": matching_rule[1],
                }
            ],
        },
        "conn": conn,
        "burst": BURST,
        "delay": DELAY,
    }


@pytest.fixture(params=("single", "double", "rev-order"))
def variation(request):
    """Have rate_limit once or twice (and in different order) in chain"""

    return request.param


@pytest.fixture(params=("service", "global"))
def key_scope(request):
    """scope of the rate_limit 'key scope' can be either 'service' or 'global'"""

    return request.param


@pytest.fixture(params=(("==", "yes"), ("matches", "y..")), ids=("eq", "RE"))
def matching_rule(request):
    """Matching rule can either compare equality or match regular expression"""

    return request.param


@pytest.fixture(scope="module")
def backend_default(private_base_url, custom_backend):
    """
    Default backend with url from private_base_url.
    Change api_backend to httpbin for service, as the test uses utilities provided
    only by http_bin ("/response_headers" endpoint)"
    """
    return custom_backend("backend_default", endpoint=private_base_url("mockserver"))


@pytest.fixture
def app2(service_plus, custom_application, custom_app_plan, lifecycle_hooks, request):
    """In case of 'global' key_scope two application are needed to ensure
    connection limiter works properly"""
    plan = custom_app_plan(rawobj.ApplicationPlan(blame(request, "aplan")), service_plus)
    return custom_application(rawobj.Application(blame(request, "app"), plan), hooks=lifecycle_hooks)


@pytest.fixture
async def client(application):
    """client needs to wait more than WAIT time"""
    async with application.api_client() as client:
        client.timeout = httpx.Timeout(WAIT + DELAY + 9.0)
        # pylint: disable=protected-access
        # no public interface to this, not sure this particular change helps
        # too early to build one (maybe after couple of months or a year of
        # presence of this comment here
        client._status_forcelist.add(502)
        yield client


@pytest.fixture
async def client2(key_scope, request):
    """A client of app2 to verify 'global' key_scope functionality"""

    if key_scope == "global":
        # this is a trick to create app2 just for 'global' scope when needed
        app2 = request.getfixturevalue("app2")
        async with app2.api_client() as client:
            client.timeout = httpx.Timeout(WAIT + DELAY + 9.0)
            # pylint: disable=protected-access
            # no public interface to this, not sure this particular change helps
            # too early to build one (maybe after couple of months or a year of
            # presence of this comment here
            client._status_forcelist.add(502)
            yield client
    else:
        yield


@pytest.fixture(scope="module", autouse=True)
def setup_async_client(lifecycle_hooks):
    """Use async api client"""
    lifecycle_hooks.append(AsyncClientHook(False))
