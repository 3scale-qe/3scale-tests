"""
Test for Account search based on spec/ui_specs/users/users_search_spec.rb
"""
import pytest

from testsuite import rawobj
from testsuite.ui.views.admin.audience.account import AccountsView
from testsuite.utils import blame

pytestmark = pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-5486")


@pytest.fixture(scope="module")
def ui_application(service, custom_app_plan, custom_ui_application, request):
    """Create an application through UI"""

    def _ui_application(account):
        name = blame(request, "ui_account")
        plan = custom_app_plan(rawobj.ApplicationPlan(blame(request, "aplan")), service)
        return custom_ui_application(name, "description", plan, account, service)

    return _ui_application


# pylint: disable=unused-argument
@pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-6205")
def test_search_account(login, navigator, custom_ui_account, ui_application, request):
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
    username = blame(request, "username")
    org_name = blame(request, "org_name")
    email = f"{username}@anything.invalid"
    account = custom_ui_account(username, email, "123456", org_name)
    app = ui_application(account)
    accounts = navigator.navigate(AccountsView)

    for key in [org_name, username, email, app["name"]]:
        accounts.search(key)
        assert accounts.table.row()[1].text == org_name
        assert accounts.table.row().state.text == "Approved"
        accounts.search("")


@pytest.fixture(scope="module")
def custom_account(custom_account, request):
    """
    Parametrized custom Account
    """
    def _custom(name):
        custom_account({
            "org_name": name,
            "username": blame(request, "username"),
            "email": f"{blame(request, 'email')}@anything.invalid",
            "password": "123456",
        })

    return _custom


# pylint: disable=unused-argument
def test_search_multiple_accounts(login, navigator, custom_account, request):
    """
    Preparation:
        - Create 4 custom account
    Test if:
        - you search account by base name it will return the correct ones (first 3)
        - you search account by specific name it will return the correct one
    """
    name = blame(request, "org_name")
    custom_account(name)
    custom_account(f"{name}_name1")
    custom_account(f"{name}_name2")
    custom_account("Organization")

    accounts = navigator.navigate(AccountsView)
    accounts.search(name)

    accounts = navigator.navigate(AccountsView)
    accounts.search(name)

    assert len(list(accounts.table.rows())) == 3

    accounts.search(f"{name}_name2")
    assert accounts.table.row()[1].text == f"{name}_name2"
    assert accounts.table.row().state.text == "Approved"


def test_search_non_existing_value(request, login, navigator, custom_account):
    """
    Preparation:
        - Create custom account
    Test if:
        - you search account by non-existing-value it won't return anything
    """
    username = blame(request, "username")
    params = {
        "org_name": blame(request, "org_name"),
        "username": username,
        "email": f"{blame(request, 'email')}@anything.invalid",
        "password": "123456",
    }
    custom_account(params)

    accounts = navigator.navigate(AccountsView)
    accounts.search("non-existing-value")

    assert next(accounts.table.rows())[0].text == "No results."


# pylint: disable=unused-argument
@pytest.mark.xfail
@pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-8468")
def test_search_short_keyword(login, navigator, custom_account, request):
    """
    Preparation:
        - Create custom account with short keyword (less than 3 characters)
    Test if:
        - you search account by specific org_name it will return the correct one
    """
    org_name = blame(request, "org-cz")
    params = {
        "org_name": org_name,
        "username": blame(request, "username"),
        "email": f"{blame(request, 'email')}@anything.invalid",
        "password": "123456",
    }
    custom_account(params)
    accounts = navigator.navigate(AccountsView)

    accounts.search(org_name)
    assert accounts.table.row()[1].text == org_name
    assert accounts.table.row().state.text == "Approved"
