"""
When the statuscode overwrite policy is configured to overwrite
certain response codes from backend, and another policy modifying the
response code is defined after it, the status code overwrite does not
affect the response code of the other policy.
"""

import pytest
from packaging.version import Version  # noqa # pylint: disable=unused-import
from testsuite import TESTED_VERSION, rawobj # noqa # pylint: disable=unused-import

pytestmark = [pytest.mark.skipif("TESTED_VERSION < Version('2.11')"),
              pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-6255")]


@pytest.fixture(scope="module")
def service(service):
    """
    Service configured with payload_limits policy after the statuscode_overwrite policy
    """
    service.proxy.list().policies.append(
        rawobj.PolicyConfig("statuscode_overwrite",
                            {"http_statuses": [
                                {"upstream": 413,
                                 "apicast": 414
                                 }]}))

    service.proxy.list().policies.append(
        rawobj.PolicyConfig("payload_limits", {"response": 100}))

    return service


def test_statuscode_overwrite(api_client):
    """
    Sends request producing response with body larger than allowed by the
    payload_limits policy.
    Asserts that the 413 response code produced by the payload_limits policy
    is not rewritten by the status_code_overwrite policy defined before it.
    """
    response = api_client().get(f"/bytes/{101}")
    assert response.status_code == 413
