"""
Rewrite of spec/ui_specs/users/users_search_spec.rb
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


# pylint: disable=unused-argument
def test_search_multiple_accounts(login, navigator, custom_account, request):
    """
    Preparation:
        - Create 4 custom account
    Test if:
        - you search account by base name it will return the correct ones (first 3)
        - you search account by specific name it will return the correct one
    """
    name = blame(request, "")
    params = [dict(org_name=f"{name}_name", username="username", email="email@anything.invalid", password="123456"),
              dict(org_name=f"{name}_name2", username="username2", email="email2@anything.invalid", password="123456"),
              dict(org_name=f"{name}", username="user", email="mail@anything.valid", password="123456"),
              dict(org_name=blame(request, "RedHat"), username="random", email="random@random.random",
                   password="123456")
              ]
    for param in params:
        custom_account(param)

    accounts = navigator.navigate(AccountsView)
    accounts.search(name)

    rows = accounts.table.rows()
    assert len(list(rows)) == 3

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
    params = dict(org_name="org_name", username=username, email=f"{blame(request, 'email')}@anything.invalid",
                  password="123456")
    custom_account(params)

    accounts = navigator.navigate(AccountsView)
    accounts.search("non-existing-value")

    assert next(accounts.table.rows())[0].text == "No results."
