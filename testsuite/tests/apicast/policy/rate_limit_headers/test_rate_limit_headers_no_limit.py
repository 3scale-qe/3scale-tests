"""
When no limit is specified, the RateLimit headers should not be contained in the response
"""

from packaging.version import Version
import pytest
from testsuite.utils import blame
from testsuite import rawobj
from testsuite import TESTED_VERSION


# rate-limit have been always unstable, likely because of overhead in staging apicast?
pytestmark = [
    pytest.mark.skipif(TESTED_VERSION < Version("2.9"), reason="TESTED_VERSION < Version('2.9')"),
    pytest.mark.flaky,
]


@pytest.fixture(scope="module")
def app_plan(service, custom_app_plan, request):
    """Default application plan"""
    return custom_app_plan(rawobj.ApplicationPlan(blame(request, "aplan")), service)


def test_rate_limit_headers_no_limit(api_client):
    """
    Sends a request to a plan without a limit
    Assert that the RateLimit headers are not contained
    """
    response = api_client().get("/anything")
    assert response.status_code == 200
    assert "RateLimit-Limit" not in response.headers
    assert "RateLimit-Remaining" not in response.headers
    assert "RateLimit-Reset" not in response.headers
