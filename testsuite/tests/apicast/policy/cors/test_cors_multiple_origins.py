"""
Tests the cors policy configured to allow multiple origins based on a regex value.
When the "origin" header matches the regex, the "Access-Control-Allow-Origin" header
is set to the value of the "origin" header.
If not, the "Access-Control-Allow-Origin" is not set. This case is not tested here, as all the
backends we are using are setting the "Access-Control-Allow-Origin", and the case is covered
by a unit test.
"""

import pytest
from packaging.version import Version  # noqa # pylint: disable=unused-import

from testsuite import TESTED_VERSION # noqa # pylint: disable=unused-import
from testsuite import rawobj

pytestmark = [
              pytest.mark.skipif("TESTED_VERSION < Version('2.10')"),
              pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-6569"),
             ]


@pytest.fixture(scope="module")
def policy_settings():
    """
    Configure the cors policy to set the "Access-Control-Allow-Origin" based on the given regex.
    """
    return rawobj.PolicyConfig("cors", {
        "allow_methods": ["GET", "POST"],
        "allow_credentials": True,
        "allow_origin": "(foo|bar).example.com"
        })


def test_cors_headers_for_same_origin(api_client):
    """
    Sends a url in "origin" header matching the regex.
    Asserts that the "Access-Control-Allow-Origin" response header is set to the
    value of the request "origin" header.
    """
    response = api_client().get("/get", headers=dict(origin="foo.example.com"))
    assert response.headers.get("Access-Control-Allow-Origin") == "foo.example.com"
