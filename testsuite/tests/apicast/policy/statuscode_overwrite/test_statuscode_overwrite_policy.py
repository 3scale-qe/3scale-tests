"""
When the statuscode overwrite policy is configured to overwrite
certain response codes from backend, the response codes are overwritten.
"""

import pytest
from packaging.version import Version  # noqa # pylint: disable=unused-import
from testsuite import TESTED_VERSION, rawobj  # noqa # pylint: disable=unused-import

pytestmark = [
    pytest.mark.skipif("TESTED_VERSION < Version('2.11')"),
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-6255"),
]


@pytest.fixture(scope="module")
def policy_settings():
    """
    Configure the statuscode overwrite policy to rewrite 202 to 203
    and 405 to 406
    """
    return rawobj.PolicyConfig(
        "statuscode_overwrite",
        {"http_statuses": [{"upstream": 202, "apicast": 203}, {"upstream": 405, "apicast": 406}]},
    )


@pytest.mark.parametrize("upstream_code,apicast_code", [(200, 200), (202, 203), (203, 203), (405, 406)])
def test_statuscode_overwrite(upstream_code, apicast_code, api_client):
    """
    Sends request to backend producing "upstream_code" response code.
    Asserts that the response codes configured to be rewritten are rewritten and the
    response that are not configured to be rewritten are left intact.
    """
    response = api_client().get(f"/status/{upstream_code}")
    assert response.status_code == apicast_code
