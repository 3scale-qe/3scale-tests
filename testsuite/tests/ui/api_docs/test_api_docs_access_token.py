"""Test API Docs access token validation: https://issues.redhat.com/browse/THREESCALE-7084"""
import pytest

from testsuite import rawobj
from testsuite.ui.views.admin.settings.api_docs import APIDocsView


@pytest.fixture(scope="module")
def valid_access_token(testconfig):
    """Valid access token"""
    return testconfig["threescale"]["admin"]["token"], "200"


@pytest.fixture(scope="module")
def invalid_access_token():
    """Invalid access token"""
    return "invalid token", "403"


# pylint: disable=unused-argument
@pytest.mark.parametrize("access_token", ["valid_access_token", "invalid_access_token"])
def test_invalid_token(request, login, navigator, access_token):
    """
    Send request via API docs `Authentication Providers Admin Portal List` endpoint
    should return status code 200 for valid access token and 403 for invalid one.
    """
    api_docs = navigator.navigate(APIDocsView)
    token = request.getfixturevalue(access_token)[0]
    code = request.getfixturevalue(access_token)[1]
    status_code = api_docs\
        .endpoint("Authentication Providers Admin Portal List")\
        .send_request(rawobj.ApiDocParams(token))
    assert status_code == code
