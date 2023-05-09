"""
A policy that allows you to reject incoming requests with a specified status code and message.
This policy should override others and reject all requests.
Expected: to return specified code eg 328 and message of service unavailability.
"""

from typing import Tuple

import pytest
import pytest_cases

from packaging.version import Version  # noqa # pylint: disable=unused-import

from testsuite import TESTED_VERSION, rawobj  # noqa # pylint: disable=unused-import
from testsuite.tests.apicast.policy.maintenance_mode import config_cases_path


pytestmark = [
    pytest.mark.skipif("TESTED_VERSION < Version('2.11')"),
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-6552"),
]


@pytest_cases.fixture
@pytest_cases.parametrize_with_cases("case_data", cases=config_cases_path)
def config(case_data, service) -> Tuple[int, int, str]:
    """returns the policy object with the specified configuration"""
    status_code_test, status_code_get, message, policy_config = case_data
    service.proxy.list().policies.append(rawobj.PolicyConfig("maintenance_mode", policy_config))
    return status_code_test, status_code_get, message


def test_maintenance_mode_policy(config, application):
    """Test request to service with maintenance_mode set returns appropriate message and status code"""
    api_client = application.api_client()
    status_code_test, status_code_get, message = config

    request = api_client.get("/test")
    assert request.status_code == status_code_test
    assert request.text == message

    request = api_client.get("/get")
    assert request.status_code == status_code_get
