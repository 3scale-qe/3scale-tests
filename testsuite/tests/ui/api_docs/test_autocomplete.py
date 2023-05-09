"""Rewrite of spec/ui_specs/autocomplete_spec.rb"""
import pytest

from testsuite import rawobj
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
    endpoint = api_docs_page.endpoint("Service Read")
    endpoint.fill(rawobj.ApiDocParams(token))
    endpoint.get_param("service_ids").click()

    product_id_element = api_docs_page.get_id_input_by_name(service["name"])
    auto_comp_prod_id = product_id_element.text
    product_id_element.click()
    assert auto_comp_prod_id == str(service["id"])

    endpoint.submit_button.click()
    assert endpoint.status_code() == "200"
