"""
    Tests that test the tenant modification such as creation, deletion, edit or resume.
"""
import pytest

from testsuite import resilient
from testsuite.ui.views.admin.login import LoginView
from testsuite.ui.views.admin.foundation import DashboardView
from testsuite.ui.views.common.foundation import NotFoundView
from testsuite.utils import blame
from testsuite.ui.utils import assert_displayed_in_new_tab
from testsuite.ui.views.master.audience.tenant import TenantDetailView, TenantEditView, TenantsView
from testsuite.ui.views.devel import LandingView

pytestmark = pytest.mark.usefixtures("master_login")


@pytest.fixture(scope="module")
def tenant_name(request):
    """ creates a simple blame string """
    return blame(request, "org-name")


@pytest.fixture(scope="module")
def ui_tenant(tenant_name, custom_ui_tenant):
    """ Overrides the ui_tenant fixture and creates and returns new tenant """
    return custom_ui_tenant(username=tenant_name, email=tenant_name, password="12345678", organisation=tenant_name)


@pytest.fixture(scope="module")
def tenant(custom_tenant):
    """Returns tenant created via api"""
    return custom_tenant()


def test_create_tenant(ui_tenant, tenant_name, navigator, browser, master_threescale):
    """
    Test:
        - Creates tenant via UI
        - Checks whether it exists
    """
    account_id = ui_tenant.entity['signup']['account']['id']
    account = master_threescale.accounts.read(account_id)

    assert account.entity_name == tenant_name

    detail_view = navigator.navigate(TenantDetailView, account=account)

    assert detail_view.public_domain.text == account.entity['domain']
    assert detail_view.admin_domain.text == account.entity['admin_domain']

    assert_displayed_in_new_tab(browser, detail_view.open_public_domain, LandingView)
    assert_displayed_in_new_tab(browser, detail_view.open_admin_domain, DashboardView)


def test_edit_tenant(navigator, tenant, master_threescale, request):
    """
    Test:
        - Create tenant via API
        - Edit tenant via UI
        - check whether it was edited
    """
    account_id = tenant.entity['signup']['account']['id']
    account = master_threescale.accounts.read(account_id)

    old_name = account.entity_name
    edit = navigator.navigate(TenantEditView, account=account)

    updated_name = blame(request, "updated_name")
    edit.update(org_name=updated_name)
    account = master_threescale.accounts.read(account_id)

    assert account.entity_name != old_name
    assert account.entity_name == updated_name


def test_delete_tenant(navigator, master_threescale, custom_tenant, browser):
    """
    Test:
        - Create tenant via API without auto-clean
        - Delete tenant via UI
        - Assert that deleted tenant is deleted
    """

    tenant = custom_tenant(autoclean=False)
    account_id = tenant.entity['signup']['account']['id']
    account = master_threescale.accounts.read(account_id)

    edit = navigator.navigate(TenantEditView, account=account)
    edit.delete()

    detail_view = navigator.navigate(TenantDetailView, account=tenant)

    account_deleted = resilient.resource_read_by_name(master_threescale.accounts, account.entity_name)
    assert account_deleted.entity['state'] == 'scheduled_for_deletion'

    assert_displayed_in_new_tab(browser, detail_view.open_public_domain, NotFoundView)
    assert_displayed_in_new_tab(browser, detail_view.open_admin_domain, NotFoundView)


def test_resume_tenant(navigator, master_threescale, tenant, browser):
    """
    Test:
        - Create and Delete tenant via API
        - Resume the deleted tenant.
        - Assert that the resume was successful
    """

    account_id = tenant.entity['signup']['account']['id']
    account = master_threescale.accounts.read(account_id)
    tenant.delete()

    detail_view = navigator.navigate(TenantDetailView, account=tenant)

    # resume tenant from deletion
    detail_view.resume()

    account_deleted = resilient.resource_read_by_name(master_threescale.accounts, account.entity_name)
    assert account_deleted.entity['state'] != 'scheduled_for_deletion'

    assert_displayed_in_new_tab(browser, detail_view.open_public_domain, LandingView)
    assert_displayed_in_new_tab(browser, detail_view.open_admin_domain, LoginView)


def test_impersonate_tenant(navigator, master_threescale, tenant, browser):
    """
    Test check impersonation functionality:
        - create tenant
        - login into master portal
        - impersonate new created tenant
        - assert that the impersonation was successful
            - dashboard is displayed
            - url is correct
    """
    account_id = tenant.entity['signup']['account']['id']
    account = master_threescale.accounts.read(account_id)

    tenants_view = navigator.navigate(TenantsView)
    tenants_view.impersonate(account)
    admin_dashboard = DashboardView(browser)
    assert account["admin_domain"] in browser.url
    assert admin_dashboard.is_displayed
