"""Configuration for mTLS tests"""

import pytest


@pytest.fixture(
    scope="module",
    params=[
        pytest.param(("valid_authority", 200), id="Matching authorities"),
        pytest.param(("invalid_authority", 502), id="Mismatched authorities"),
    ],
)
def authority_and_code(request):
    """
    Returns authority for httpbin and return code it should return
    """
    return request.getfixturevalue(request.param[0]), request.param[1]


@pytest.fixture(scope="module")
def upstream_authority(authority_and_code):
    """
    Authority of the upstream API used to the validation of the requests from APIcast
    """
    authority, _ = authority_and_code
    return authority
