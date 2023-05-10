"""Conftest for special char tests"""
import pytest

PATHS = ["/", "/foo/"]


@pytest.fixture(scope="module", params=PATHS)
def backend_path(request):
    """Path to the backend"""
    return request.param


@pytest.fixture(scope="module")
def backends_mapping(private_base_url, custom_backend):
    """
    For each path create separate backend

    It needs to point to HTTPBIN_GO! Only httpbin go is not decoding the url
    """

    return {path: custom_backend(endpoint=private_base_url("httpbin_go")) for path in PATHS}
