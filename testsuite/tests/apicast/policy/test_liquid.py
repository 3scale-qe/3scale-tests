"""
Test behavior of liquid
"""

import pytest
from packaging.version import Version

from testsuite import TESTED_VERSION, rawobj

pytestmark = [
    pytest.mark.skipif(TESTED_VERSION <= Version("2.13"), reason="TESTED_VERSION <= Version('2.13')"),
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-8483"),
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-8484"),
]


@pytest.fixture(scope="module")
def policy_settings():
    """configures headers in policy"""
    return rawobj.PolicyConfig(
        "headers",
        {
            "response": [
                {
                    "op": "set",
                    "header": "X-Liquid-String-Doesnt-Contain",
                    "value_type": "liquid",
                    "value": '{% if "abcdef" contains "wxyz" %}fail{% else %}pass{% endif %}',
                },
                {
                    "op": "set",
                    "header": "X-Liquid-String-Contains",
                    "value_type": "liquid",
                    "value": '{% if "abcdef" contains "bcd" %}pass{% else %}fail{% endif %}',
                },
                {
                    "op": "set",
                    "header": "X-Liquid-Array-Doesnt-Contain",
                    "value_type": "liquid",
                    "value": '{% assign arr = "abcd afooa efghi" | split: " " %}{% if arr contains "foo" %}fail{% else %}pass{% endif%}',  # noqa # pylint: disable=line-too-long
                },
                {
                    "op": "set",
                    "header": "X-Liquid-Array-Contains",
                    "value_type": "liquid",
                    "value": '{% assign arr = "abcd foo efghi" | split: " " %}{% if arr contains "foo" %}pass{% else %}fail{% endif%}',  # noqa # pylint: disable=line-too-long
                },
            ]
        },
    )


@pytest.fixture(scope="module")
def response(api_client):
    """Make one request for all tests"""
    return api_client().get("/get")


def test_liquid_string_doesnt_contain(response):
    """Test liquid 'contains' condition on string that doesn't match"""
    assert response.headers.get("X-Liquid-String-Doesnt-Contain", "HEADER IS MISSING") == "pass"


def test_liquid_string_contains(response):
    """Test liquid 'contains' condition on string that matches"""
    assert response.headers.get("X-Liquid-String-Contains", "HEADER IS MISSING") == "pass"


def test_liquid_array_doesnt_contain(response):
    """Test liquid 'contains' condition on array that doesn't match"""
    assert response.headers.get("X-Liquid-Array-Doesnt-Contain", "HEADER IS MISSING") == "pass"


def test_liquid_array_contains(response):
    """Test liquid 'contains' condition on array that matches"""
    assert response.headers.get("X-Liquid-Array-Contains", "HEADER IS MISSING") == "pass"
