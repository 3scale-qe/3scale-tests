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
from concurrent.futures.thread import ThreadPoolExecutor

import backoff
import pytest
from pytest_cases import fixture_plus, fixture_ref, parametrize_plus, cases_data

from testsuite import rawobj
from testsuite.gateways.gateways import Capability
from testsuite.tests.apicast.policy.rate_limit.leaky_bucket import config_cases
from testsuite.utils import blame

TOTAL_REQUESTS = 6


@fixture_plus
def service(service_proxy_settings, custom_service, request):
    """Service configured with config"""
    return custom_service({"name": blame(request, "svc")}, service_proxy_settings)


@fixture_plus
def service2(service_proxy_settings, custom_service, request):
    """Service configured with parametrized config"""
    return custom_service({"name": blame(request, "svc")}, service_proxy_settings)


@fixture_plus
@parametrize_plus('svc,scope',
                  [(fixture_ref(service), "service"), (fixture_ref(service2), "global")])
@cases_data(module=config_cases)
def config(svc, scope, case_data, service, service2):
    """Configuration for rate limit policy"""
    policy_config, apply_rate_limit = case_data.get(scope)
    service.proxy.list().policies.append(policy_config)
    service2.proxy.list().policies.append(policy_config)
    return apply_rate_limit, svc


@fixture_plus
def application(service, custom_app_plan, custom_application, request):
    """First application bound to the account and service_plus"""
    plan = custom_app_plan(rawobj.ApplicationPlan(blame(request, "aplan")), service)
    return custom_application(rawobj.Application(blame(request, "app"), plan))


@fixture_plus
def application2(config, custom_app_plan, custom_application, request):
    """Second application bound to the account and service_plus"""
    svc = config[1]
    plan = custom_app_plan(rawobj.ApplicationPlan(blame(request, "aplan")), svc)
    return custom_application(rawobj.Application(blame(request, "app"), plan))


@backoff.on_predicate(backoff.constant, lambda x: x[0], 20)
def retry_requests(client, client2, rate_limit_applied):
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
    loop = asyncio.get_event_loop()
    responses = []
    with ThreadPoolExecutor(max_workers=TOTAL_REQUESTS + 1) as pool:
        futures = []
        for _ in range(TOTAL_REQUESTS // 2):
            futures.append(loop.run_in_executor(pool, client.get, "/get"))
            futures.append(loop.run_in_executor(pool, client2.get, "/get"))
        responses = loop.run_until_complete(asyncio.gather(*futures))

    status_codes = [response.status_code for response in responses]
    if rate_limit_applied:
        return status_codes.count(429) == 0, status_codes
    return status_codes.count(200) == 6, status_codes


@pytest.mark.required_capabilities(Capability.SAME_CLUSTER)
def test_leaky_bucket(application, application2, config):
    """
    Test rate limit policy with leaky bucket limiters configurations.
    This test is the same for the different configuration which are specified in the config_cases.py file.
    Based on the config[0] value, this test method tests:
        - True: the rate limit was applied to requests (at least one request should be rejected)
        - False: the rate limit was not applied to requests  (every requests should be successful)
    :param application: first application
    :param application2: second application
    :param config: configuration of the actual test
    """
    client = application.api_client()
    client2 = application2.api_client()
    status_codes = retry_requests(client, client2, config[0])[1]

    successful = status_codes.count(200)
    if config[0]:  # is the condition of the leaky bucket limiter true?
        assert successful >= 2  # at least 2 requests should be successful
        assert status_codes.count(429) >= 1  # at least 1 requests should be rejected
    else:
        assert successful == TOTAL_REQUESTS  # all responses should be 200
