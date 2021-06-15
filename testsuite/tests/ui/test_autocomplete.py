"""Rewrite of spec/ui_specs/autocomplete_spec.rb"""
from testsuite.ui.views.admin.settings.api_docs import APIDocsView
from testsuite.utils import blame


# pylint: disable=unused-argument
def test_autocomplete(testconfig, custom_ui_product, request, navigator, login):
    """
        A test that checks whether autocomplete works as expected on API Docs

        - creates a service (product) that will be used in auto-complete
        - goes to API Docs and searches for "Service Read" category
        - fills out "Service Read" arguments and then sends it to server
        - checks whether all went as expected
    """
    name = blame(request, "name")
    system_name = blame(request, "system_name")
    product = custom_ui_product(name, system_name, "description")

    token = testconfig["threescale"]["admin"]["token"]

    api_docs_page = navigator.navigate(APIDocsView)
    assert api_docs_page.is_displayed
    assert api_docs_page.endpoint_section("Service Read").wait_displayed()

    endpoint = api_docs_page.endpoint_section("Service Read")
    endpoint.unroll()
    endpoint.fill_input("access_token", token)
    endpoint.get_input_field("service_ids").click()

    product_id_element = api_docs_page.get_id_input_by_name(product["name"])
    auto_comp_prod_id = product_id_element.text
    product_id_element.click()
    assert auto_comp_prod_id == str(product["id"])

    endpoint.submit_button.click()
    assert endpoint.status_code.wait_displayed()
    assert endpoint.status_code.text == "200"
