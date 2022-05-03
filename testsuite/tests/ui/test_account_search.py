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
        assert accounts.table.row()[5].text == "Approved"
