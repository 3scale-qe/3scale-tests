"""
Configuration for maintenance mode policy test
This file contains different cases for testing.
Every case function have parameter which can be used to configure and test the policy
"""

from typing import Tuple
from urllib.parse import urlparse


def case_eq_host(status_code, private_base_url) -> Tuple[int, str, dict]:
    """Case path on maintenance"""
    message = "Echo API /test is currently Unavailable"
    policy_config = {
        "condition": {"operations": [
            {"left_type": "liquid",
             "right_type": "plain",
             "left": "{{ upstream.host }}",
             "right": urlparse(private_base_url("echo_api")).hostname,
             "op": "=="}], "combine_op": "or"},
        "status": status_code,
        "message": message
        }

    return status_code, f"{message}\n", policy_config


def case_matches_host(status_code) -> Tuple[int, str, dict]:
    """Case regex path on maintenance"""
    message = "Echo API /test is currently Unavailable"
    policy_config = {
        "condition": {"operations": [
            {"left_type": "liquid",
             "right_type": "plain",
             "left": "{{ upstream.host }}",
             "right": "echo-api",
             "op": "matches"}], "combine_op": "or"},
        "status": status_code,
        "message": message
        }

    return status_code, f"{message}\n", policy_config


def case_matches_path(status_code) -> Tuple[int, str, dict]:
    """Case path on maintenance"""
    message = "Service Unavailable - Maintenance"
    policy_config = {
        "condition": {"operations": [
            {"left_type": "liquid",
             "right_type": "plain",
             "left": "{{ upstream.path }}",
             "right": "test",
             "op": "matches"}], "combine_op": "or"},
        "status": status_code,
        "message": message
        }

    return status_code, f"{message}\n", policy_config
