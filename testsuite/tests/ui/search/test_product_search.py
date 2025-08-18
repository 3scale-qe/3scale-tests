"""
Test for product search
"""

import pytest
from packaging.version import Version

from testsuite import TESTED_VERSION
from testsuite.ui.views.admin.product import ProductsView
from testsuite.utils import blame

pytestmark = [
    pytest.mark.usefixtures("login"),
    pytest.mark.skipif(TESTED_VERSION < Version("2.14-dev"), reason="TESTED_VERSION < Version('2.14-dev')"),
]


@pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-8562")
def test_search_product(navigator, request, custom_ui_product):
    """
    Preparation:
        - Create custom product
    Test if:
        - you search product by name it will return the correct one
        - you search product by system name it will return the correct one
    """
    name = blame(request, "name")
    sys_name = blame(request, "system")
    custom_ui_product(name, sys_name)
    products = navigator.navigate(ProductsView)

    for key in [name, sys_name]:
        products.search(key)
        assert products.table.row()[0].text == name
        assert products.table.row()[1].text == sys_name


def test_search_multiple_products(navigator, custom_service, request):
    """
    Preparation:
        - Create 4 custom products
    Test if:
        - you search product by base name it will return the correct ones (first 3)
        - you search product by specific name it will return the correct one
    """
    name = blame(request, "product")
    params = [f"{name}_name", f"{name}_name2", f"{name}", blame(request, "RedHat")]
    for param in params:
        custom_service({"name": param})

    products = navigator.navigate(ProductsView)
    products.search(name)

    assert len(list(products.table.rows())) == 3

    products.search(f"{name}_name2")
    assert products.table.row()[0].text == f"{name}_name2"


def test_search_non_existing_value(request, navigator, custom_service):
    """
    Preparation:
        - Create custom product
    Test if:
        - you search product by non-existing-value it won't return anything
    """
    custom_service({"name": blame(request, "product")})

    products = navigator.navigate(ProductsView)
    products.search("non-existing-value")

    assert len(list(products.table.rows())) == 0
