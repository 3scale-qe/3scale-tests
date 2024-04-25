"""
A policy that allows you to reject incoming requests with a specified status code and message.
This policy should override others and reject all requests.
Expected: to return specified code eg 328 and message of service unavailability.
"""

from typing import Tuple
from urllib.parse import urlparse

import pytest
import pytest_cases

from packaging.version import Version  # noqa # pylint: disable=unused-import

from testsuite import TESTED_VERSION, rawobj  # noqa # pylint: disable=unused-import
from testsuite.tests.apicast.policy.maintenance_mode import config_cases_host


pytestmark = [
    pytest.mark.skipif("TESTED_VERSION < Version('2.11')"),
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-6552"),
]


@pytest.fixture
def echo_api_base_url(private_base_url):
    """Return URL of echo_api"""
    return private_base_url("echo_api")


@pytest.fixture
def backend_bin(custom_backend, private_base_url):
    """Httpbin backend"""
    return custom_backend("backend_bin", endpoint=private_base_url("httpbin"))


@pytest.fixture
def backend_echo(custom_backend, echo_api_base_url):
    """Echo-api backend"""
    return custom_backend("backend_echo", endpoint=echo_api_base_url)


@pytest.fixture
def backends_mapping(backend_bin, backend_echo):
    """
    Create 2 separate backends echo and httpbin
    """
    return {"/test/echo": backend_echo, "/bin": backend_bin}


@pytest.fixture
def mapping_rules(service, backend_bin, backend_echo):
    """
    Backend echo:
        - Add mapping rule with path "/anything/test"
    Backend httpbin:
        - Add mapping rule with path "/anything/bin"
    """
    proxy = service.proxy.list()
    proxy.mapping_rules.list()[0].delete()

    test_metric = backend_echo.metrics.list()[0]
    bin_metric = backend_bin.metrics.list()[0]
    backend_echo.mapping_rules.create(rawobj.Mapping(test_metric, "/anything/test"))
    backend_bin.mapping_rules.create(rawobj.Mapping(bin_metric, "/anything/bin"))
    proxy.deploy()


@pytest.fixture
def policy_settings_alt(service, echo_api_base_url) -> dict:
    """set the maintenance mode policy before Apicast in the chain"""
    service = service.proxy.list().policies.insert(
        0,
        rawobj.PolicyConfig(
            "maintenance_mode",
            {
                "condition": {
                    "operations": [
                        {
                            "left_type": "liquid",
                            "right_type": "plain",
                            "left": "{{ upstream.host }}",
                            "right": urlparse(echo_api_base_url).hostname.split(".", 1)[0],
                            "op": "matches",
                        }
                    ],
                    "combine_op": "or",
                },
                "status": 328,
                "message": "SERVICE UNAVAILABLE",
            },
        ),
    )

    return service


@pytest_cases.fixture
@pytest_cases.parametrize_with_cases("case_data", cases=config_cases_host)
def config(case_data, service) -> Tuple[int, str]:
    """returns the policy object with the specified configuration"""
    status_code, message, policy_config = case_data
    service.proxy.list().policies.append(rawobj.PolicyConfig("maintenance_mode", policy_config))
    return status_code, message


def test_maintenance_mode_policy(config, application):
    """Test request to service with maintenance_mode set returns appropriate message and status code"""
    api_client = application.api_client()
    status_code, message = config

    request = api_client.get("/test/echo/anything/test")
    assert request.status_code == status_code
    assert request.text == message

    request = api_client.get("/bin/anything/bin")
    assert request.status_code == 200


# pylint: disable=unused-argument
def test_maintenance_mode_policy_failure(policy_settings_alt, application):
    """Test that maintenance mode fails to check upstream host if the policy is placed
    before apicast.
    The fixture 'policy_settings_alt' configure the policy chain placing the maintenance
    mode policy before apicast.
    """
    api_client = application.api_client()

    request = api_client.get("/test/echo/anything/test")
    assert request.status_code == 200
