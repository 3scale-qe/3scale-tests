"""Test for field definitions issue"""
# pylint: disable=unused-argument
import pytest
from widgetastic.widget import TextInput

from testsuite.ui.views.admin.audience.account_user import AccountUserEditView, AccountUserDetailView
from testsuite.ui.views.admin.audience.fields_definitions import FieldsDefinitionsCreateView


@pytest.fixture
def fields_definitions(login, navigator, threescale):
    """Create custom field definition"""
    page = navigator.navigate(FieldsDefinitionsCreateView)
    page.create_definition("custom_field", "Contact Name")
    definition = [x for x in threescale.fields_definitions.list() if x["name"] == "custom_field"][0]
    yield definition
    threescale.fields_definitions.delete(definition.entity_id)


@pytest.mark.xfail
@pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-7955")
def test_field_definitions(fields_definitions, account, navigator, browser):
    """
    Preparation:
        - Create custom field definition
    Test:
        - navigate to AccountUserEditView
        - edit custom field
        - navigate to AccountUserDetailView
        - assert that custom field is displayed and correctly edited
    """
    user = account.users.list()[0]
    user_edit = navigator.navigate(AccountUserEditView, account=account, user=user)
    field = TextInput(browser, id='user_extra_fields_custom_field')
    field.fill('anything')
    user_edit.update_button.click()
    navigator.navigate(AccountUserDetailView, account=account, user=user)
    assert browser.element(".//th[contains(text(),'Contact Name')]").is_displayed()
    assert browser.element(".//td[contains(text(),'anything')]").is_displayed()
