"""
Rewrite: ./spec/ui_specs/wizard_spec.rb
"""
from urllib.parse import urlparse

import pytest

from testsuite.ui.views.admin.wizard import (
    WizardIntroView,
    WizardBackendApiView,
    WizardRequestView,
    WizardEditApiView,
    WizardResponseView,
    WizardOutroView,
)
from testsuite.utils import blame

pytestmark = pytest.mark.usefixtures("login")


def test_wizard_correct_request(navigator, request, private_base_url):
    """
    Test:
    - Fill wizard with correct data
    - Assert if values are displayed in examples
    - Send request to backend API
    - Assert that response page is displayed with successful request
    - Assert that wizard outer page is displayed
    """
    backend_url = private_base_url("echo_api")
    backend_name = blame(request, "backend-name")
    product_name = blame(request, "product-name")
    backend_path = "/whatever"
    navigator.open(WizardIntroView)
    request_page = navigator.navigate(
        WizardRequestView, backend_name=backend_name, base_url=backend_url, product_name=product_name, path=backend_path
    )
    request_page.method_field.fill("/some/path")
    assert request_page.method_field.value == "/some/path"
    assert request_page.request_example_path.text == "/some/path"
    assert request_page.feedback_example_path.text == "/some/path"
    assert urlparse(backend_url).hostname in request_page.backend_url_example.text
    response_view = navigator.navigate(WizardResponseView)
    assert response_view.page_title.text == "Congratulations, you are running on 3scale :-)"
    outro_view = navigator.navigate(WizardOutroView)
    assert outro_view.is_displayed


def test_wizard_bad_request(navigator, request, private_base_url):
    """
    Test:
    - Fill wizard with wrong data
    - Send request to backend API
    - Assert that response page is displayed with unsuccessful request
    - Edit api with correct backend API
    - Assert that response page is displayed with successful request
    """
    wrong_backend_url = "https://wrong_url.invalid"
    correct_backend_url = private_base_url("echo_api")
    backend_name = blame(request, "backend-name")
    product_name = blame(request, "product-name")
    backend_path = "/whatever"
    navigator.open(WizardIntroView)
    response_view = navigator.navigate(
        WizardResponseView,
        backend_name=backend_name,
        base_url=wrong_backend_url,
        product_name=product_name,
        path=backend_path,
    )
    assert response_view.page_title.text == "Oops, Test request failed with HTTP code 503"
    response_view.try_again(url=correct_backend_url)
    assert response_view.page_title.text == "Congratulations, you are running on 3scale :-)"


def test_wizard_set_default_backend_url(navigator):
    """
    Test:
    - Set predefined url to backend  by 3scale
    - Assert that predefined url is correct
    """
    navigator.open(WizardIntroView)
    add_backend_page = navigator.navigate(WizardBackendApiView)
    add_backend_page.set_echo_api()
    assert add_backend_page.base_url_field.value == "https://echo-api.3scale.net"


def test_wizard_link_to_product(navigator, request, browser, private_base_url):
    """
    Test:
    - Fill wizard with correct data
    - Edit API from request page
    - Assert Edit API page is displayed and product name is correct
    - Navigate to next page
    - Assert that request page is displayed
    """
    backend_url = private_base_url("echo_api")
    backend_name = blame(request, "backend-name")
    product_name = blame(request, "product-name")
    backend_path = "/whatever"
    navigator.open(WizardIntroView)
    request_page = navigator.navigate(
        WizardRequestView, backend_name=backend_name, base_url=backend_url, product_name=product_name, path=backend_path
    )
    request_page.edit_api_btn.click()
    edit_api_view = WizardEditApiView(browser)
    assert edit_api_view.is_displayed
    assert edit_api_view.product_name_field.value == product_name
    edit_api_view.update_api_btn.click()
    assert request_page.is_displayed
