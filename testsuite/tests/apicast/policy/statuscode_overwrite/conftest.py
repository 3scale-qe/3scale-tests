"""Default conftest for statuscode overwrite"""

import pytest


@pytest.fixture(scope="module")
def backend_default(private_base_url, custom_backend):
    """
    Default backend with url from private_base_url.
    Status code overwrite are using httpbin endpoints
    """
    return custom_backend("backend_default", endpoint=private_base_url("httpbin"))
