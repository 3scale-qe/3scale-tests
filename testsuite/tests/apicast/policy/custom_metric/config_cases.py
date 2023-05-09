"""
Configuration for custom metric policy test
This file contains different cases for testing.
"""

from typing import Tuple, List
from testsuite import rawobj


def case_simple() -> Tuple[dict, List[tuple], List[str]]:
    """
    Case with a condition matching 403 status code
    """
    policy = custom_metrics_policy([rule(condition())])
    calls = [call(403, [1]), call(402, [0])]
    metrics = ["foo"]
    return policy, calls, metrics


def case_header_increment() -> Tuple[dict, List[tuple], List[str]]:
    """
    Case matching a 200 status code, incrementing by the value sent in the 'increment' header in the
    upstream API response
    """
    policy = custom_metrics_policy([rule(condition(left="200"), increment="{{ resp.headers['increment'] }}")])
    calls = [
        call(200, [1], "/response-headers", {"increment": [1]}),
        call(200, [10], "/response-headers", {"increment": [10]}),
    ]
    metrics = ["foo"]
    return policy, calls, metrics


def case_matches() -> Tuple[dict, List[tuple], List[str]]:
    """
    Case matching based on the regular expressions (PCRE)
    """
    policy = custom_metrics_policy(
        [rule(condition(left="{{status}}", left_type="liquid", right="4..", right_type="plain", operation="matches"))]
    )
    calls = [call(403, [1]), call(402, [1]), call(500, [0])]
    metrics = ["foo"]
    return policy, calls, metrics


def case_matches_multiple_rules() -> Tuple[dict, List[tuple], List[str]]:
    """
    Case with a multiple rules incrementing multiple metrics at once
    """
    policy = custom_metrics_policy(
        [rule(condition(left="200"), "foo"), rule(condition(left="200"), "foo_{{status}}", "2")]
    )
    metrics = ["foo", "foo_200"]
    calls = [call(200, increments=[1, 2])]
    return policy, calls, metrics


def case_liquid_filter() -> Tuple[dict, List[tuple], List[str]]:
    """
    Case incrementing the metric based on the liquid filtering and the status code value
    """
    policy = custom_metrics_policy([rule(condition("1", "plain", "1", "plain"), "foo_{{status}}")])
    metrics = ["foo_200", "foo_201"]
    calls = [call(200, increments=[1, 0]), call(201, increments=[0, 1])]
    return policy, calls, metrics


def call(status_code, increments=None, endpoint: str = None, params: dict = None):
    """
    function returning a 4-tuple of values used to test one request
    """
    increments = increments or [1]
    endpoint = endpoint or "/status/" + str(status_code)
    params = params or {}
    return status_code, increments, endpoint, params


def condition(right="{{status}}", right_type="liquid", left="403", left_type="plain", operation="=="):
    """
    The condition that the policy uses to match the requests
    """
    return {
        "operations": [
            {"right": right, "right_type": right_type, "left": left, "left_type": left_type, "op": operation}
        ],
        "combine_op": "and",
    }


def rule(cond, metric="foo", increment="1"):
    """
    A rule for the custom metric policy
    """
    return {"metric": metric, "increment": increment, "condition": cond, "combine_op": "and"}


def custom_metrics_policy(rules):
    """
    Returns the object representing the configured custom metric policy
    """
    return rawobj.PolicyConfig("custom_metrics", {"rules": rules})
