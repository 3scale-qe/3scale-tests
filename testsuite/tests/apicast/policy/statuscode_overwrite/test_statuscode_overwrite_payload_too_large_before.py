"""
When the statuscode overwrite policy is configured to overwrite
certain response codes from backend, and another policy modifying the
response code is configured before it, the status code overwrite is applied
on the response code produced by the second policy.
"""

import pytest
from packaging.version import Version

from testsuite import TESTED_VERSION, rawobj

pytestmark = [
    pytest.mark.skipif(TESTED_VERSION < Version("2.11"), reason="TESTED_VERSION < Version('2.11')"),
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-6255"),
]


@pytest.fixture(scope="module")
def service(service):
    """
    Service configured with payload_limits policy before the statuscode_overwrite policy
    """
    service.proxy.list().policies.append(rawobj.PolicyConfig("payload_limits", {"response": 100}))
    service.proxy.list().policies.append(
        rawobj.PolicyConfig("statuscode_overwrite", {"http_statuses": [{"upstream": 413, "apicast": 414}]})
    )
    return service


def test_statuscode_overwrite(api_client):
    """
    Sends request producing response with body larger than allowed by the
    payload_limits policy.
    Asserts that the 413 response code produced by the payload_limits policy
    is rewritten to 414 by the statuscode overwrite policy
    """
    response = api_client().get(f"/bytes/{101}")
    assert response.status_code == 414
