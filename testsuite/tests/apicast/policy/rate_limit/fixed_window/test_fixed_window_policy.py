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
import pytest_cases
from pytest_cases import parametrize_with_cases
from testsuite import rawobj
from testsuite.capabilities import Capability
from testsuite.tests.apicast.policy.rate_limit.fixed_window import config_cases
from testsuite.utils import blame


pytestmark = pytest.mark.flaky


@pytest_cases.fixture
def service_plus2(service_proxy_settings, custom_service, request, backends_mapping):
    """Service configured with parametrized config"""
    service = custom_service({"name": blame(request, "svc")}, service_proxy_settings, backends_mapping)
    yield service
    for usage in service.backend_usages.list():
        usage.delete()


@pytest_cases.fixture
@parametrize_with_cases("case_data", cases=config_cases)
def config(case_data, service_plus, service_plus2):
    """Configuration for rate limit policy"""
    policy_config, status_code, scope = case_data
    service_plus.proxy.list().policies.append(policy_config)
    service_plus2.proxy.list().policies.append(policy_config)
    # When scope=service we want 2 application for same service
    if scope == "service":
        return status_code, service_plus
    # when scope=global we want 1 application for each service
    return status_code, service_plus2


@pytest_cases.fixture
def application2(config, custom_app_plan, custom_application, request):
    """Second application bound to the account and service_plus"""
    service = config[1]
    plan = custom_app_plan(rawobj.ApplicationPlan(blame(request, "aplan")), service)
    return custom_application(rawobj.Application(blame(request, "app"), plan))


@pytest_cases.fixture
def client(application):
    """
    client for first application.
    """

    client = application.api_client()
    yield client
    client.close()


@pytest_cases.fixture
def client2(application2):
    """
    client for second application.
    """

    client = application2.api_client()
    yield client
    client.close()


@backoff.on_predicate(backoff.constant, lambda x: x[0] != 429 or x[1] != 429, max_time=config_cases.TIME_WINDOW)
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
def test_fixed_window(client, client2, config):
    """
    Test global fixed window test different configurations with global scope based on configuration cases
    If the condition in the configuration is true:
        (status_code = 429) it should return 429 for both applications
    if the condition in the configuration is false:
        (status_code = 200) it should keep returning 200 for both applications
    """
    status_code = config[0]
    for _ in range(config_cases.DEFAULT_COUNT // 2):
        assert client.get("/get").status_code == 200
        assert client2.get("/get").status_code == 200

    # skip if status_code 200 is expected
    # (condition of the policy is false and the requests should keep returning 200)
    if status_code != 200:
        code_1, code_2 = retry_requests(client, client2)
        assert code_1 == status_code
        assert code_2 == status_code
        time.sleep(config_cases.TIME_WINDOW)

    assert client.get("/get").status_code == 200
    assert client2.get("/get").status_code == 200
