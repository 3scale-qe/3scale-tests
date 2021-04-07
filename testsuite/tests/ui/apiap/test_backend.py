"""Rewrite of spec/ui_specs/api_as_a_product/create_backend_spec.rb.rb"""
import pytest

from testsuite.ui.views.admin.backends import BackendEditView
from testsuite.utils import blame


def test_create_backend(custom_ui_backend, request):
    """
    Test:
        - Create backend via UI
        - Assert that name is correct
        - Assert that system_name is correct
        - Assert that description is correct
        - Assert that endpoint is correct
    """
    name = blame(request, "name")
    system_name = blame(request, "system_name")
    backend = custom_ui_backend(name, system_name, "description", "https://anything.invalid:443")
    assert backend["name"] == name
    assert backend["system_name"] == system_name
    assert backend["description"] == "description"
    assert backend["private_endpoint"] == "https://anything.invalid:443"


# pylint: disable=unused-argument
def test_edit_backend(login, navigator, custom_backend, threescale):
    """
    Test:
        - Create backend via API
        - Edit backend via UI
        - Assert that name is correct
        - Assert that description is correct
        - Assert that endpoint is correct
    """
    backend = custom_backend()
    edit = navigator.navigate(BackendEditView, backend=backend)

    edit.update("updated_name", "updated_description", "https://updated_endpoint")
    backend = threescale.backends.read_by_name(backend.entity_name)

    assert backend["name"] == "updated_name"
    assert backend["description"] == "updated_description"
    assert backend["private_endpoint"] == "https://updated_endpoint:443"


# pylint: disable=unused-argument
def test_delete_backend(login, navigator, threescale, custom_backend):
    """
    Test:
        - Create backend via API without autoclean
        - Delete backend via UI
        - Assert that deleted backend no longer exists
    """
    backend = custom_backend(autoclean=False)
    edit = navigator.navigate(BackendEditView, backend=backend)
    edit.delete()
    backend = threescale.backends.read_by_name(backend.entity_name)

    assert backend is None


@pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-3571")
def test_delete_used_backend(service, login, navigator, threescale):
    """
    Test:
        - Create service with backend via API
        - Assert that used backend cannot be deleted
    """
    backend_id = service.backend_usages.list()[0]["backend_id"]
    backend = threescale.backends.read(backend_id)
    edit = navigator.navigate(BackendEditView, backend=backend)
    assert not edit.delete_button.is_displayed
