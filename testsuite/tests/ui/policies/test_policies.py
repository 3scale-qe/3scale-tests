"""Rewrite of spec/ui_specs/policies_spec.rb"""
import pytest

from testsuite.ui.views.admin.product.integration.configuration import ProductConfigurationView
from testsuite.ui.views.admin.product.integration.policies import ProductPoliciesView, Policies

pytestmark = pytest.mark.usefixtures("login")


def test_add_policy(navigator, policy_service):
    """
    Test:
        - Create service via API
        - Navigate to Policies page and add Echo policy via UI
        - Assert that policy was added
        - Update policy chain and assert that configuration out of date is displayed
        - Navigate to Configuration page and promote configuration to staging
    """
    policies_page = navigator.navigate(ProductPoliciesView, product=policy_service)
    policies_page.add_policy(Policies.ECHO.value)
    assert policies_page.policy_section.has_item(Policies.ECHO.value)
    policies_page.update_policy_chain_button.click()
    assert policies_page.outdated_config.is_displayed
    configuration_page = navigator.navigate(ProductConfigurationView, product=policy_service)
    assert configuration_page.configuration.staging_promote_btn.is_enabled
    configuration_page.configuration.staging_promote_btn.click()
    assert not configuration_page.configuration.staging_promote_btn.is_enabled


def test_remove_policy(navigator, policy_service):
    """
    Test:
        - Create service via API
        - Navigate to Policies page and add Echo policy via UI
        - Remove Echo policy from policy chain
        - Assert that policy was removed
    """
    policies_page = navigator.navigate(ProductPoliciesView, product=policy_service)
    policies_page.add_policy(Policies.ECHO.value)
    assert policies_page.policy_section.has_item(Policies.ECHO.value)
    policies_page.update_policy_chain_button.click()
    assert policies_page.outdated_config.is_displayed
    policies_page.remove_policy(Policies.ECHO.value)
    assert not policies_page.policy_section.has_item(Policies.ECHO.value)
    policies_page.update_policy_chain_button.click()
    assert not policies_page.policy_section.has_item(Policies.ECHO.value)


def test_apply_and_remove_policy(navigator, policy_service, api_client, policy_application):
    """
        Test:
            - Create service via API
            - Navigate to Policies page and add Echo policy via UI
            - Assert that policy was added and is applied
            - Remove Echo policy from policy chain
            - Assert that policy was removed
            - Assert that api call works without policy
        """
    policies_page = navigator.navigate(ProductPoliciesView, product=policy_service)
    policies_page.add_policy(Policies.ECHO.value)
    assert policies_page.policy_section.has_item(Policies.ECHO.value)
    policies_page.policy_section.edit_policy(Policies.ECHO.value)
    policies_page.echo_policy_view.edit_echo_policy(status_code=333)
    policies_page.policy_section.drag_and_drop_policy(source=Policies.ECHO.value,
                                                      destination=Policies.THREESCALE_APICAST.value)
    policies_page.update_policy_chain_button.click()

    configuration_page = navigator.navigate(ProductConfigurationView, product=policy_service)
    configuration_page.configuration.staging_promote_btn.click()
    response = api_client(app=policy_application).get('/anything')
    assert response.status_code == 333

    policies_page = navigator.navigate(ProductPoliciesView, product=policy_service)
    assert policies_page.policy_section.has_item(Policies.ECHO.value)
    policies_page.remove_policy(Policies.ECHO.value)
    policies_page.update_policy_chain_button.click()
    assert not policies_page.policy_section.has_item(Policies.ECHO.value)

    configuration_page = navigator.navigate(ProductConfigurationView, product=policy_service)
    configuration_page.configuration.staging_promote_btn.click()
    response = api_client(app=policy_application).get('/anything')
    assert response.status_code == 200


def test_move_policy(navigator, policy_service, api_client, policy_application):
    """
    Test:
        - Create service via API
        - Navigate to Policies page and add Echo policy with changed status code via UI
        - Assert that API call returns 200 With APICast policy first in policy chain
        - Move Echo policy to top of policy chain
        - Assert that moving policy triggers promoting apicast action
        - Assert that Echo policy is applied via API call
    """
    policies_page = navigator.navigate(ProductPoliciesView, product=policy_service)
    policies_page.add_policy(Policies.ECHO.value)
    assert policies_page.policy_section.has_item(Policies.ECHO.value)
    policies_page.policy_section.edit_policy(Policies.ECHO.value)
    policies_page.echo_policy_view.edit_echo_policy(status_code=333)

    assert policies_page.policy_section.first_policy == Policies.THREESCALE_APICAST.value
    policies_page.update_policy_chain_button.click()

    configuration_page = navigator.navigate(ProductConfigurationView, product=policy_service)
    assert configuration_page.configuration.staging_promote_btn.is_enabled
    configuration_page.configuration.staging_promote_btn.click()
    response = api_client(app=policy_application).get('/anything')
    assert response.status_code == 200

    policies_page = navigator.navigate(ProductPoliciesView, product=policy_service)
    policies_page.policy_section.drag_and_drop_policy(source=Policies.ECHO.value,
                                                      destination=Policies.THREESCALE_APICAST.value)
    assert policies_page.policy_section.first_policy == Policies.ECHO.value
    policies_page.update_policy_chain_button.click()
    assert policies_page.outdated_config.is_displayed
    configuration_page = navigator.navigate(ProductConfigurationView, product=policy_service)
    configuration_page.configuration.staging_promote_btn.click()

    response = api_client(app=policy_application).get('/anything')
    assert response.status_code == 333


def test_edit_policy_widgets(navigator, policy_service, api_client, policy_application):
    """
    Test:
        - Create service via API
        - Navigate to Policies page and add URL Rewriting policy with rewriting command via UI
        - Assert that policy was added and is applied
        - Navigate to the configuration page and promote new configuration to the staging phase
        - Fetch product policies
        - Assert that new URL Rewriting policy configuration was successfully applied
        - Assert that new URL Rewriting policy correctly modifying path
    """
    policies_page = navigator.navigate(ProductPoliciesView, product=policy_service)
    policies_page.add_policy(Policies.URL_REWRITING.value)
    assert policies_page.policy_section.has_item(Policies.URL_REWRITING.value)

    policies_page.policy_section.edit_policy(Policies.URL_REWRITING.value)
    policies_page.url_rewrite_policy_view.add_rewriting_command(regex="hello", replace="get", operation="gsub")
    policies_page.update_policy_chain_button.click()
    assert policies_page.outdated_config.is_displayed

    configuration_page = navigator.navigate(ProductConfigurationView, product=policy_service)
    configuration_page.configuration.staging_promote_btn.click()

    policies = policy_service.proxy.list()["policies_config"]
    assert len(policies) == 2
    url_rewriting_policy = policies[1]

    assert url_rewriting_policy["name"] == "url_rewriting"
    assert url_rewriting_policy["configuration"]["commands"][0]["regex"] == "hello"
    assert url_rewriting_policy["configuration"]["commands"][0]["replace"] == "get"
    assert url_rewriting_policy["configuration"]["commands"][0]["op"] == "gsub"

    response = api_client(app=policy_application).get('/hello')
    assert response.json()["path"] == "/get"
