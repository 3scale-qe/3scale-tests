"""Rewrite of spec/ui_specs/autocomplete_spec.rb"""
import pytest

from testsuite.ui.views.admin.settings.api_docs import APIDocsView


@pytest.mark.usefixtures("login")
def test_autocomplete(navigator, service, testconfig):
    """
    A test that checks whether autocomplete works as expected on API Docs

    - creates a service (product) that will be used in auto-complete
    - goes to API Docs and searches for "Service Read" category
    - fills out "Service Read" arguments and then sends it to server
    - checks whether all went as expected
    """
    token = testconfig["threescale"]["admin"]["token"]

    api_docs_page = navigator.navigate(APIDocsView)
    endpoint = api_docs_page.endpoint("GET", "/admin/api/services/{id}.xml")
    endpoint.set_param("access_token", token)
    endpoint.set_param("id", service["name"])

    id_column = endpoint.get_param("id")
    assert endpoint.extract_text(id_column) == str(service["id"])

    endpoint.execute()
    assert endpoint.status_code == "200"
