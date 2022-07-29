"""
Rewrite of spec/ui_specs/users/users_search_spec.rb
"""
import pytest

from testsuite.ui.views.admin.product import ProductsView
from testsuite.utils import blame


# pylint: disable=unused-argument
@pytest.mark.xfail
@pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-8562")
def test_search_product(login, navigator, request, custom_ui_product):
    """
    Preparation:
        - Create custom account
        - Create custom application
    Test if:
        - you search account by org_name it will return the correct one
        - you search account by username it will return the correct one
        - you search account by email it will return the correct one
        - you search account by application name  it will return the correct one
    """
    name = blame(request, "name")
    sys_name = blame(request, "system")
    custom_ui_product(name, sys_name)
    products = navigator.navigate(ProductsView)

    for key in [name, sys_name]:
        products.search(key)
        assert products.table.row()[0].text == name
        assert products.table.row()[1].text == sys_name


# pylint: disable=unused-argument
def test_search_multiple_products(login, navigator, custom_service, request):
    """
    Preparation:
        - Create 4 custom services
    Test if:
        - you search account by base name it will return the correct ones (first 3)
        - you search account by specific name it will return the correct one
    """
    name = blame(request, "")
    params = [f"{name}_name", f"{name}_name2", f"{name}", blame(request, "RedHat")]
    for param in params:
        custom_service({"name": param})

    products = navigator.navigate(ProductsView)
    products.search(name)

    assert len(list(products.table.rows())) == 3

    products.search(f"{name}_name2")
    assert products.table.row()[0].text == f"{name}_name2"


def test_search_non_existing_value(request, login, navigator, custom_service):
    """
    Preparation:
        - Create custom service
    Test if:
        - you search account by non-existing-value it won't return anything
    """
    custom_service({"name": blame(request, "service")})

    products = navigator.navigate(ProductsView)
    products.search("non-existing-value")

    assert len(list(products.table.rows())) == 0
