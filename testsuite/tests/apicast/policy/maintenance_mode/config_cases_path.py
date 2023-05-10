"""
Configuration for maintenance mode policy test
This file contains different cases for testing.
Every case function have parameter which can be used to configure and test the policy
"""

from typing import Tuple


def case_eq_path(status_code) -> Tuple[int, int, str, dict]:
    """Case path on maintenance"""
    message = "Echo API /test is currently Unavailable"
    policy_config = {
        "condition": {
            "operations": [
                {
                    "left_type": "liquid",
                    "right_type": "plain",
                    "left": "{{ original_request.path }}",
                    "right": "/test",
                    "op": "==",
                }
            ],
            "combine_op": "and",
        },
        "status": status_code,
        "message": message,
    }

    return status_code, 200, f"{message}\n", policy_config


def case_match_path(status_code) -> Tuple[int, int, str, dict]:
    """Case regex path on maintenance"""
    message = "Echo API /test is currently Unavailable"
    policy_config = {
        "condition": {
            "operations": [
                {
                    "left_type": "liquid",
                    "right_type": "plain",
                    "left": "{{ original_request.path }}",
                    "right": "/te",
                    "op": "matches",
                }
            ],
            "combine_op": "and",
        },
        "status": status_code,
        "message": message,
    }

    return status_code, 200, f"{message}\n", policy_config


def case_service_maintenance(status_code) -> Tuple[int, int, str, dict]:
    """Case whole service on maintenance"""
    message = "Service Unavailable - Maintenance"
    policy_config = {"status": status_code, "message": message, "message_content_type": "text/plain; charset=utf-8"}

    return status_code, status_code, f"{message}\n", policy_config
