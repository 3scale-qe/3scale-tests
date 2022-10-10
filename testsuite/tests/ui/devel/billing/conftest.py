"""Conftest for billing tests"""
import pytest
from threescale_api.resources import InvoiceState

from testsuite import rawobj
from testsuite.ui.objects import BillingAddress
from testsuite.ui.views.admin.audience.account import InvoiceDetailView
from testsuite.ui.views.admin.audience.billing import BillingSettingsView
from testsuite.utils import randomize


@pytest.fixture
def line_items():
    """List of all items to be added to an invoice"""
    return [{'name': "test-item", 'description': 'test_item', 'quantity': '1', 'cost': 10}]


@pytest.fixture
def api_invoice(account, threescale, line_items):
    """Invoice created through API"""
    invoice = threescale.invoices.create(dict(account_id=account['id']))
    for line_item in line_items:
        invoice.line_items.create(line_item)

    invoice.state_update(InvoiceState.PENDING)
    invoice.charge()
    return invoice


@pytest.fixture
def ui_invoice(custom_admin_login, navigator, account, line_items, threescale):
    """Invoice created through UI"""
    custom_admin_login()
    view = navigator.navigate(InvoiceDetailView, account=account)
    for line_item in line_items:
        view.add_item(**line_item)

    view.issue()
    invoice = threescale.invoices.list_by_account(account)[0]
    view.charge(invoice)
    return invoice


@pytest.fixture(scope="module")
def billing_address():
    """Billing Address for Credit Card details"""
    return BillingAddress("Red Hat", "Street 5", "Bratislava", "Slovakia", "", "123456789", "12345")


@pytest.fixture(scope="module")
def stripe_gateway(custom_admin_login, navigator, testconfig):
    """Enables Stripe billing gateway"""
    custom_admin_login()
    billing = navigator.navigate(BillingSettingsView)
    billing.charging(True)
    billing.stripe(testconfig["stripe"]["secret_key"],
                   testconfig["stripe"]["publishable_key"],
                   "empty-webhook")


@pytest.fixture(scope="module")
def braintree_gateway(custom_admin_login, navigator, testconfig, braintree):
    """
    Enables Braintree billing gateway.
    Args:
        :param sca: enable or disable SCA for the gateway; possible values True or False
    """
    def _braintree(sca):
        custom_admin_login()
        billing = navigator.navigate(BillingSettingsView)
        billing.charging(True)
        currency = braintree.merchant_currency()
        billing.charging_form.change_currency(currency)
        billing.braintree(testconfig["braintree"]["public_key"],
                          testconfig["braintree"]["merchant_id"],
                          testconfig["braintree"]["private_key"],
                          sca)

    return _braintree


@pytest.fixture(scope="module")
def braintree_gateway_sca(braintree_gateway):
    """Ensures Braintree billing gateway with SCA enabled"""
    braintree_gateway(True)


@pytest.fixture(scope="module")
def braintree_gateway_no_sca(braintree_gateway):
    """Ensures Braintree billing gateway with SCA disabled"""
    braintree_gateway(False)


@pytest.fixture(scope="module")
def account(threescale, custom_account, request, account_password):
    """Preconfigured account existing over whole testing session"""
    iname = randomize("id")
    account = rawobj.Account(org_name=iname, monthly_billing_enabled=False, monthly_charging_enabled=False)
    account.update(dict(
        name=iname, username=iname,
        email=f"{iname}@anything.invalid",
        password=account_password))

    def _cancel_invoices():
        """If the tests fails and the invoices are kept open, it wont remove the account until they are cancelled"""
        for invoice in threescale.invoices.list_by_account(account):
            if invoice["state"] == InvoiceState.OPEN.value or invoice["state"] == InvoiceState.PENDING.value:
                invoice.state_update(InvoiceState.CANCELLED)

    request.addfinalizer(_cancel_invoices)
    account = custom_account(params=account)

    return account
