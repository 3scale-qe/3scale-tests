"""Rewrite of spec/ui_specs/api_as_a_product/create_service_spec.rb"""
import pytest

from testsuite.ui.views.admin.product import ProductEditView
from testsuite.utils import blame


@pytest.fixture(scope="module")
def product(request, service_proxy_settings, custom_service, lifecycle_hooks):
    """Create custom service that will be deleted during test run"""
    return custom_service({"name": blame(request, "svc")}, service_proxy_settings, hooks=lifecycle_hooks,
                          autoclean=False)


def test_create_product(custom_ui_product, request):
    """
    Test:
        - Create product via UI
        - Assert that name is correct
        - Assert that system_name is correct
        - Assert that description is correct
    """
    name = blame(request, "name")
    system_name = blame(request, "system_name")
    product = custom_ui_product(name, system_name, "description")
    assert product["name"] == name
    assert product["system_name"] == system_name
    assert product["description"] == "description"


# pylint: disable=unused-argument
def test_edit_product(login, navigator, service, threescale):
    """
    Test:
        - Create service via API
        - Edit service via UI
        - Assert that name is correct
        - Assert that description is correct
    """
    edit = navigator.navigate(ProductEditView, product=service)

    edit.update("updated_name", "updated_description")
    product = threescale.services.read_by_name(service.entity_name)

    assert product["name"] == "updated_name"
    assert product["description"] == "updated_description"


# pylint: disable=unused-argument
def test_delete_product(login, navigator, threescale, product):
    """
    Test:
        - Create product via API without autoclean
        - Delete product via UI
        - Assert that deleted product no longer exists
    """
    edit = navigator.navigate(ProductEditView, product=product)
    edit.delete()
    product = threescale.services.read_by_name(product.entity_name)

    assert product is None
