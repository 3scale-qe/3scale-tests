"""
Test that deletion of product don't delete backend used by another product
"""

import pytest

from testsuite.utils import blame


@pytest.fixture(scope="module")
def backends_mapping(custom_backend):
    """
    :return: dict in format {path: backend}
    """
    return {"/test": custom_backend("backend")}


def test_products_with_same_backend(service, custom_service, threescale, backends_mapping, request):
    """
    Preparation:
        - Create 2 products
        - Create backend
        - Add backend to both products
    Test if:
        - both products have same backend
        - second product still have backend after deletion of first product
    """
    service2 = custom_service({"name": blame(request, "svc")}, backends=backends_mapping, autoclean=False)
    backends1 = service.backend_usages.list()
    backends2 = service2.backend_usages.list()
    backend1 = threescale.backends.read(backends1[0]["backend_id"])
    backend2 = threescale.backends.read(backends2[0]["backend_id"])

    assert backend1["name"] == backend2["name"]

    service2.delete()

    assert len(service.backend_usages.list()) != 0
