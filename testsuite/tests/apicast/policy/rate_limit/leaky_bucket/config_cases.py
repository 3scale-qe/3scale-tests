"""
    Configuration cases for leaky bucket policy tests
    Each case_ function is used as policy configuration for test
                        returns tuple: 1st: configuration of the policies
                                       2nd: True if the condition was applied, false otherwise
"""
from typing import Tuple

from pytest_cases import parametrize

from testsuite import rawobj
from testsuite.utils import randomize

DEFAULT_RATE = 1
DEFAULT_BURST = 1


@parametrize("scope", ["service", "global"])
def case_matching_simple(scope: str, redis_url) -> Tuple[dict, bool, str]:
    """Simple case of leaky bucket limiter with matching condition"""
    configuration = [config(operation_conf(), scope)]
    policy_config = leaky_bucket_policy(configuration, redis_url(scope))
    return policy_config, True, scope


@parametrize("scope", ["service", "global"])
def case_matching_liquid_simple(scope: str, redis_url) -> Tuple[dict, bool, str]:
    """Case with matching condition using liquid"""
    configuration = [
        config(operation_conf(operation="matches", left="{{ uri }}", left_type="liquid", right="/.*"), scope)
    ]
    policy_config = leaky_bucket_policy(configuration, redis_url(scope))
    return policy_config, True, scope


@parametrize("scope", ["service", "global"])
def case_matching_multiple(scope: str, redis_url) -> Tuple[dict, bool, str]:
    """
    Case with 2 leaky bucket limiters with matching condition
        First leaky bucket limiter:
                                    rate=1
                                    burst=1
        Second leaky bucket limiter:
                                    rate=10
                                    burst=0
    """
    configuration = [config(operation_conf(), scope), config(operation_conf(), scope, rate=10, burst=0)]
    policy_config = leaky_bucket_policy(configuration, redis_url(scope))
    return policy_config, True, scope


@parametrize("scope", ["service", "global"])
def case_matching_prepend_multiple(scope: str, redis_url) -> Tuple[dict, bool, str]:
    """
    Case with 2 leaky bucket limiters with matching condition
        First leaky bucket limiter:
                                    rate=10
                                    burst=0
        Second leaky bucket limiter:
                                    rate=1
                                    burst=1
    """
    configuration = [config(operation_conf(), scope, rate=10, burst=0), config(operation_conf(), scope)]
    policy_config = leaky_bucket_policy(configuration, redis_url(scope))
    return policy_config, True, scope


@parametrize("scope", ["service", "global"])
def case_non_matching_simple(scope: str, redis_url) -> Tuple[dict, bool, str]:
    """Simple case of leaky bucket limiter with non matching condition. The rate limit should not be applied."""
    configuration = [config(operation_conf(operation="!="), scope)]
    policy_config = leaky_bucket_policy(configuration, redis_url(scope))
    return policy_config, False, scope


@parametrize("scope", ["service", "global"])
def case_non_matching_liquid_simple(scope: str, redis_url) -> Tuple[dict, bool, str]:
    """Case with non matching condition using liquid. The rate limit should not be applied."""
    configuration = [
        config(
            operation_conf(operation="matches", left="{{ uri }}", left_type="liquid", right="/does_not_exist"), scope
        )
    ]
    policy_config = leaky_bucket_policy(configuration, redis_url(scope))
    return policy_config, False, scope


@parametrize("scope", ["service", "global"])
def case_non_matching_multiple(scope: str, redis_url) -> Tuple[dict, bool, str]:
    """
    Case with 2 leaky bucket limiters with non matching condition
        First leaky bucket limiter:
                                    rate=1
                                    burst=1
        Second leaky bucket limiter:
                                    rate=10
                                    burst=0
    The rate limit should not be applied.
    """
    configuration = [
        config(operation_conf(operation="!="), scope),
        config(operation_conf(operation="!="), scope, rate=10, burst=0),
    ]
    policy_config = leaky_bucket_policy(configuration, redis_url(scope))
    return policy_config, False, scope


@parametrize("scope", ["service", "global"])
def case_non_matching_prepend_multiple(scope: str, redis_url) -> Tuple[dict, bool, str]:
    """
    Case with 2 leaky bucket limiters with non matching condition
        First leaky bucket limiter:
                                    rate=10
                                    burst=0
        Second leaky bucket limiter:
                                    rate=1
                                    burst=1
    The rate limit should not be applied.
    """
    configuration = [
        config(operation_conf(operation="!="), scope, rate=10, burst=0),
        config(operation_conf(operation="!="), scope),
    ]
    policy_config = leaky_bucket_policy(configuration, redis_url(scope))
    return policy_config, False, scope


def leaky_bucket_policy(leaky_bucket_limiters, redis_url):
    """Creates PolicyConfig dictionary for rate limits with leaky bucket limiters"""
    return rawobj.PolicyConfig(
        "rate_limit",
        {
            "leaky_bucket_limiters": leaky_bucket_limiters,
            "limits_exceeded_error": {},
            "configuration_error": {},
            "redis_url": redis_url,
        },
    )


def config(operation, scope, rate=DEFAULT_RATE, burst=DEFAULT_BURST):
    """Configuration for fixed window with specific condition and count for window"""
    return {
        "condition": {"condition_op": "and", "operations": [operation]},
        "key": {"scope": scope, "name": randomize("leaky_bucket"), "name_type": "plain"},
        "rate": rate,
        "burst": burst,
    }


def operation_conf(operation="matches", right="1", right_type="plain", left="1", left_type="plain"):
    """Operation configuration for rate limit policies"""
    return {"left": left, "left_type": left_type, "op": operation, "right": right, "right_type": right_type}
