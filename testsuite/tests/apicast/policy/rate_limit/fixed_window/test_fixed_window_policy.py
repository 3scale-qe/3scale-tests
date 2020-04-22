"""
Rewrite of rate limit fixed window specs (both true/false and global/service) + added new combinations
spec/functional_specs/policies/rate_limit/fixed_window/
    false_condition/rate_limit_window_global_false_spec.rb
    false_condition/rate_limit_multiple_windows_global_false_spec.rb
    false_condition/rate_limit_multiple_prepend_windows_global_false_spec.rb
    false_condition/rate_limit_window_service_false_spec.rb
    false_condition/rate_limit_multiple_windows_service_false_spec.rb
    true_condition/rate_limit_window_global_true_spec.rb
    true_condition/rate_limit_multiple_windows_global_true_spec.rb
    true_condition/rate_limit_multiple_prepend_windows_global_true_spec.rb
    true_condition/rate_limit_multiple_windows_service_true_spec.rb
    true_condition/rate_limit_window_service_true_spec.rb
    liquid/rate_limit_window_matches_false_spec.rb
    liquid/rate_limit_window_liquid_service_false_spec.rb
    liquid/rate_limit_window_matches_true_spec.rb
    liquid/rate_limit_window_liquid_service_true_spec.rb
"""
import time
import backoff
import pytest

from pytest_cases import fixture_plus, cases_data, parametrize_plus, fixture_ref
from testsuite import rawobj
from testsuite.gateways.gateways import Capability
from testsuite.tests.apicast.policy.rate_limit.fixed_window import config_cases
from testsuite.utils import blame

from ..conftest import service_plus


@fixture_plus
def service_plus2(service_proxy_settings, custom_service, request):
    """Service configured with parametrized config"""
    return custom_service({"name": blame(request, "svc")}, service_proxy_settings)


@fixture_plus
@parametrize_plus('service,scope',
                  [(fixture_ref(service_plus), "service"), (fixture_ref(service_plus2), "global")])
@cases_data(module=config_cases)
def config(service, scope, case_data, service_plus, service_plus2):
    """Configuration for rate limit policy"""
    policy_config, status_code = case_data.get(scope)
    service_plus.proxy.list().policies.append(policy_config)
    service_plus2.proxy.list().policies.append(policy_config)
    return status_code, service


@fixture_plus
def application2(config, custom_app_plan, custom_application, request):
    """Second application bound to the account and service_plus"""
    service = config[1]
    plan = custom_app_plan(rawobj.ApplicationPlan(blame(request, "aplan")), service)
    return custom_application(rawobj.Application(blame(request, "app"), plan))


@backoff.on_predicate(backoff.constant, lambda x: x[0] != 429 or x[1] != 429, config_cases.TIME_WINDOW)
def retry_requests(client, client2):
    """
    Retries request to get both status codes with value 429 in fixed window time
    :param client: first api client
    :param client2: second api client
    :return: status codes for both request in tuple
    """
    code_1 = client.get("/get").status_code
    code_2 = client2.get("/get").status_code
    return code_1, code_2


@pytest.mark.required_capabilities(Capability.SAME_CLUSTER)
def test_fixed_window(api_client, api_client2, config):
    """
    Test global fixed window test different configurations with global scope based on configuration cases
    If the condition in the configuration is true:
        (status_code = 429) it should return 429 for both applications
    if the condition in the configuration is false:
        (status_code = 200) it should keep returning 200 for both applications
    """
    status_code = config[0]
    for _ in range(config_cases.DEFAULT_COUNT // 2):
        assert api_client.get("/get").status_code == 200
        assert api_client2.get("/get").status_code == 200

    # skip if status_code 200 is expected
    # (condition of the policy is false and the requests should keep returning 200)
    if status_code != 200:
        code_1, code_2 = retry_requests(api_client, api_client2)
        assert code_1 == status_code
        assert code_2 == status_code
        time.sleep(config_cases.TIME_WINDOW)

    assert api_client.get("/get").status_code == 200
    assert api_client2.get("/get").status_code == 200
