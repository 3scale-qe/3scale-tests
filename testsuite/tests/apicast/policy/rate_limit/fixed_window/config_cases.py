"""
Configuration for fixed window policy test
This file contains different cases for testing.
Every case function have parameter which can be used for both "service" and "global" scopes
"""

from typing import Tuple

from pytest_cases import parametrize

from testsuite.config import settings
from testsuite import rawobj
from testsuite.utils import randomize

DEFAULT_COUNT = 6
TIME_WINDOW = 20


@parametrize('scope', ['service', 'global'])
def case_true_simple(scope: str) -> Tuple[dict, int, str]:
    """Simple case with true condition"""
    configuration = [config(condition(), scope)]
    policy_config = fixed_window_policy(configuration, redis_url(scope))
    status_code = 429
    return policy_config, status_code, scope


@parametrize('scope', ['service', 'global'])
def case_true_liquid_simple(scope: str) -> Tuple[dict, int, str]:
    """Case with true condition with liquid"""
    configuration = [config(condition(operation="matches", left="{{ uri }}", left_type="liquid", right="/.*"), scope)]
    policy_config = fixed_window_policy(configuration, redis_url(scope))
    status_code = 429
    return policy_config, status_code, scope


@parametrize('scope', ['service', 'global'])
def case_true_multiple(scope: str) -> Tuple[dict, int, str]:
    """Case with true condition that contains multiple fixed window limiters"""
    configuration = [config(condition(), scope), config(condition(), scope, 100)]
    policy_config = fixed_window_policy(configuration, redis_url(scope))
    status_code = 429
    return policy_config, status_code, scope


@parametrize('scope', ['service', 'global'])
def case_true_prepend_multiple(scope: str) -> Tuple[dict, int, str]:
    """Case with true condition that contains multiple prepend fixed window limiters"""
    configuration = [config(condition(), scope, 100), config(condition(), scope)]
    policy_config = fixed_window_policy(configuration, redis_url(scope))
    status_code = 429
    return policy_config, status_code, scope


@parametrize('scope', ['service', 'global'])
def case_false_simple(scope: str) -> Tuple[dict, int, str]:
    """Simple case with false condition"""
    configuration = [config(condition(operation="!="), scope)]
    policy_config = fixed_window_policy(configuration, redis_url(scope))
    status_code = 200
    return policy_config, status_code, scope


@parametrize('scope', ['service', 'global'])
def case_false_liquid_simple(scope: str) -> Tuple[dict, int, str]:
    """Case with false condition with liquid"""
    cond = condition(operation="matches", left="{{ uri }}", left_type="liquid", right="/does_not_exist")
    configuration = [config(cond, scope)]
    policy_config = fixed_window_policy(configuration, redis_url(scope))
    status_code = 200
    return policy_config, status_code, scope


@parametrize('scope', ['service', 'global'])
def case_false_multiple(scope: str) -> Tuple[dict, int, str]:
    """Case with false condition that contains multiple fixed window limiters"""
    configuration = [config(condition(operation="!="), scope), config(condition(operation="!="), scope, 100)]
    policy_config = fixed_window_policy(configuration, redis_url(scope))
    status_code = 200
    return policy_config, status_code, scope


@parametrize('scope', ['service', 'global'])
def case_false_prepend_multiple(scope: str) -> Tuple[dict, int, str]:
    """Case with false condition that contains multiple prepend fixed window limiters"""
    configuration = [config(condition(operation="!="), scope, 100), config(condition(operation="!="), scope)]
    policy_config = fixed_window_policy(configuration, redis_url(scope))
    status_code = 200
    return policy_config, status_code, scope


def fixed_window_policy(fixed_window_limiters, redis_url):
    """Creates PolicyConfig dictionary for rate limits with fixed window limiters"""
    return rawobj.PolicyConfig("rate_limit", {"fixed_window_limiters": fixed_window_limiters,
                                              "limits_exceeded_error": {},
                                              "configuration_error": {},
                                              "redis_url": redis_url})


def config(cond, scope, count=DEFAULT_COUNT):
    """Configuration for fixed window with specific condition and count for window"""
    return {
        "condition": cond,
        "window": TIME_WINDOW,
        "key": {
            "scope": scope,
            "name": randomize('fixed_window'),
            "name_type": "plain"
        },
        "count": count}


def condition(operation="matches", right="1", right_type="plain", left="1", left_type="plain"):
    """Condition for rate limit policies"""
    return {
        "condition_op": "and",
        "operations": [{
            "op": operation,
            "right": right,
            "right_type": right_type,
            "left": left,
            "left_type": left_type}]}


def redis_url(scope: str):
    """
    Redis URL if the scope is global
    empty string ("") otherwise
    """
    return settings['redis']['url'] if scope == "global" else ""
