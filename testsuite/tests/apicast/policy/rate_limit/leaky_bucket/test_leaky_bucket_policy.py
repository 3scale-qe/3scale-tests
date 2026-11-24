"""
Test whether rate limit leaky bucket controls number of simultaneous incoming requests

Rewrite:
    spec/functional_specs/policies/rate_limit/leaky_bucket/
        liquid/rate_limit_bucket_liquid_service_false_spec.rb
        liquid/rate_limit_bucket_liquid_service_true_spec.rb
        liquid/rate_limit_bucket_matches_false_spec.rb
        liquid/rate_limit_bucket_matches_true_spec.rb
        plain_text/false_condition/rate_limit_bucket_global_false_spec.rb
        false_condition/rate_limit_bucket_service_false_spec.rb
        false_condition/rate_limit_multiple_bucket_global_false_spec.rb
        false_condition/rate_limit_multiple_bucket_service_false_spec.rb
        false_condition/rate_limit_multiple_prepend_bucket_global_false_spec.rb
        true_condition/rate_limit_bucket_global_true_spec.rb
        true_condition/rate_limit_bucket_service_true_spec.rb
        true_condition/rate_limit_multiple_bucket_global_true_spec.rb
        true_condition/rate_limit_multiple_bucket_service_true_spec.rb
        true_condition/rate_limit_multiple_prepend_bucket_global_true_spec.rb
"""

import asyncio

import backoff
import httpx
import pytest
import pytest_cases
from pytest_cases import parametrize_with_cases

from testsuite import rawobj
from testsuite.capabilities import Capability
from testsuite.httpx import AsyncClientHook
from testsuite.tests.apicast.policy.rate_limit.leaky_bucket import config_cases
from testsuite.utils import blame

TOTAL_REQUESTS = 6


pytestmark = pytest.mark.flaky


@pytest.fixture(scope="module", autouse=True)
def setup_async_client(lifecycle_hooks):
    """Use async api client"""
    lifecycle_hooks.append(AsyncClientHook(False))


@pytest_cases.fixture
def service(service_proxy_settings, custom_service, request, backends_mapping):
    """Service configured with config"""
    service = custom_service({"name": blame(request, "svc")}, service_proxy_settings, backends_mapping)
    yield service
    for usage in service.backend_usages.list():
        usage.delete()


@pytest.fixture
def service2(service_proxy_settings, custom_service, request, backends_mapping):
    """Service configured with parametrized config"""
    service = custom_service({"name": blame(request, "svc")}, service_proxy_settings, backends_mapping)
    yield service
    for usage in service.backend_usages.list():
        usage.delete()


@pytest_cases.fixture
@parametrize_with_cases("case_data", cases=config_cases)
def config(case_data, service, service2):
    """Configuration for rate limit policy"""
    policy_config, apply_rate_limit, scope = case_data
    service.proxy.list().policies.append(policy_config)
    service2.proxy.list().policies.append(policy_config)
    # When scope=service we want 2 application for same service
    if scope == "service":
        return apply_rate_limit, service
    # when scope=global we want 1 application for each service
    return apply_rate_limit, service2


@pytest.fixture
def application2(config, custom_app_plan, custom_application, lifecycle_hooks, request):
    """Second application bound to the account and service_plus"""
    svc = config[1]
    plan = custom_app_plan(rawobj.ApplicationPlan(blame(request, "aplan")), svc)
    return custom_application(rawobj.Application(blame(request, "app"), plan), hooks=lifecycle_hooks)


@pytest.fixture
async def client(application):
    """api client for application"""
    async with application.api_client() as client:
        client.timeout = httpx.Timeout(TOTAL_REQUESTS * 2)
        yield client


@pytest.fixture
async def client2(application2):
    """api client for application2"""
    async with application2.api_client() as client:
        client.timeout = httpx.Timeout(TOTAL_REQUESTS * 2)
        yield client


@backoff.on_predicate(backoff.fibo, lambda x: x[0], max_tries=8, jitter=None)
async def retry_requests(client, client2, rate_limit_applied):
    """
    Retries requests to both clients
    If rate limit policy configuration was applied it will retry requests until at least one request was rejected
    otherwise it will retry requests untill each request was successful
    :param client: client of the first application
    :param client2: client of the second application
    :param rate_limit_applied: true if the condition will be true, false otherwise
    :return: tuple: 1st: boolean if this function should be repeated, false otherwise
                    2nd: list of status codes
    """
    futures = []
    for _ in range(TOTAL_REQUESTS // 2):
        futures.append(client.get("/get"))
        futures.append(client2.get("/get"))
    responses = await asyncio.gather(*futures)

    status_codes = [response.status_code for response in responses]
    if rate_limit_applied:
        return status_codes.count(429) == 0, status_codes
    return status_codes.count(200) == 6, status_codes


@pytest.mark.required_capabilities(Capability.SAME_CLUSTER)
@pytest.mark.asyncio
async def test_leaky_bucket(client, client2, config):
    """
    Test rate limit policy with leaky bucket limiters configurations.
    This test is the same for the different configuration which are specified in the config_cases.py file.
    Based on the config[0] value, this test method tests:
        - True: the rate limit was applied to requests (at least one request should be rejected)
        - False: the rate limit was not applied to requests  (every requests should be successful)
    :param client: api_client for the first application
    :param client2: api_client for the second application
    :param config: configuration of the actual test
    """
    result = await retry_requests(client, client2, config[0])
    _, status_codes = result

    successful = status_codes.count(200)
    if config[0]:  # is the condition of the leaky bucket limiter true?
        assert successful >= 2  # at least 2 requests should be successful
        assert status_codes.count(429) >= 1  # at least 1 requests should be rejected
    else:
        assert successful == TOTAL_REQUESTS  # all responses should be 200
