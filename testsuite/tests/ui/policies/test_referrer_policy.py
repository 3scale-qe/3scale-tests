"""Rewrite of spec/ui_specs/policies/referrer_policy_in_ui.rb"""

import pytest

from testsuite.ui.views.admin.audience.application import ApplicationDetailView
from testsuite.ui.views.admin.product.integration.policies import ProductPoliciesView, Policies
from testsuite.ui.views.admin.product.integration.configuration import ProductConfigurationView
from testsuite.ui.views.admin.product.application import UsageRulesView


@pytest.fixture(scope="module", autouse=True)
def referrer_policy_setup(custom_admin_login, navigator, service, application):
    """Setup service with referer policy with 'localhost' and 'localdomain' domains allowed """
    custom_admin_login()
    policies_page = navigator.navigate(ProductPoliciesView, product=service)
    policies_page.add_policy(Policies.THREESCALE_REFERRER.value)
    policies_page.update_policy_chain_button.click()
    usage_rules_page = navigator.navigate(UsageRulesView, product=service)
    usage_rules_page.referrer_filtering_checkbox.click()
    usage_rules_page.update_usage_rules()
    application_page = navigator.navigate(ApplicationDetailView, product=service,
                                          application=application)
    application_page.add_referer_filter("localhost")
    application_page.add_referer_filter("localdomain")
    configuration_page = navigator.navigate(ProductConfigurationView, product=service)
    configuration_page.configuration.staging_promote_btn.click()


@pytest.fixture()
def make_request(api_client, application):
    """Make request with additional referer header values"""
    def prepare_request(domain=None):
        headers = {"Referer": domain}
        return api_client(app=application).get('/get', headers=headers)

    return prepare_request


def test_referrer_with_valid_domain(make_request):
    """
    Test:
        - Assert that requests with allowed domains returns code 200
    """
    assert make_request("localhost").status_code == 200
    assert make_request("localdomain").status_code == 200


def test_referrer_with_first_valid(make_request):
    """
    Test:
        - Assert that requests with first allowed domains returns code 200
        - Assert that requests with second invalid domains returns code 403
        - Assert that requests with third allowed domains returns code 200
    """
    assert make_request("localhost").status_code == 200
    assert make_request("example.com").status_code == 403
    assert make_request("localhost").status_code == 200


def test_referrer_with_first_invalid(make_request):
    """
    Test:
        - Send first invalid request, then valid then invalid again and valid
    """
    assert make_request("example.com").status_code == 403
    assert make_request("localhost").status_code == 200
    assert make_request("example.com").status_code == 403
    assert make_request("localdomain").status_code == 200


def test_referrer_mixed_requests(make_request):
    """
    Test:
        - Send first request with referrer, then without and last with referrer
    """
    assert make_request("localhost").status_code == 200
    for _ in range(0, 3):
        assert make_request("example.com").status_code == 403
    assert make_request("localdomain").status_code == 200
