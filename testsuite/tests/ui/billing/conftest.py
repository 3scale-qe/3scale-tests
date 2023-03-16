"""Conftest for billing tests"""
import pytest
from threescale_api.resources import InvoiceState

from testsuite import rawobj
from testsuite.ui.objects import BillingAddress
from testsuite.ui.views.admin.audience.account import InvoiceDetailView, AccountInvoicesView
from testsuite.utils import randomize


@pytest.fixture(scope="module")
def cost():
    """A fixture that provides variable cost for the line item, thus the price of the invoice"""
    return 10


@pytest.fixture(scope="module")
def line_items(cost):
    """List of all items to be added to an invoice"""
    return [{'name': "test-item", 'description': 'test_item', 'quantity': '1', 'cost': cost}]


@pytest.fixture
def invoice(account, threescale, line_items):
    """Creates a new invoice via API."""
    account_invoices = threescale.invoices.list_by_account(account)
    invoice = threescale.invoices.create({"account_id": account['id']})
    for line_item in line_items:
        invoice.line_items.create(line_item)
    invoice = invoice.state_update(InvoiceState.PENDING)
    assert len(threescale.invoices.list_by_account(account)) - len(account_invoices) == 1
    return invoice


@pytest.fixture(scope="module")
def ui_invoice(custom_admin_login, navigator, account, line_items, threescale):
    """
    Creates and charges invoice through UI.
    Asserts if a new invoice was created and charged.
    """
    def _ui_invoice():
        custom_admin_login()
        navigator.navigate(AccountInvoicesView, account=account).create()
        invoice = threescale.invoices.list_by_account(account)
        assert len(invoice) == 1, "More than one invoice was created for an Account"

        invoice_view = navigator.navigate(InvoiceDetailView, account=account, invoice=invoice[0])
        invoice_view.add_items(line_items)
        invoice_view.issue()
        invoice_view.assert_issued()
        return invoice_view

    return _ui_invoice


@pytest.fixture(scope="module")
def billing_address():
    """Billing Address for Credit Card details"""
    return BillingAddress("Red Hat", "Street 5", "Bratislava", "Slovakia", "", "123456789", "12345")


@pytest.fixture(scope="module")
def account(threescale, custom_account, request, account_password):
    """Preconfigured account existing over whole testing session"""
    iname = randomize("id")
    account = rawobj.Account(org_name=iname, monthly_billing_enabled=False, monthly_charging_enabled=False)
    account.update(
        {
            "name": iname,
            "username": iname,
            "email": f"{iname}@anything.invalid",
            "password": account_password,
        }
    )

    def _cancel_invoices():
        """If the tests fail and the invoices are kept open, it won't remove the account until they are cancelled"""
        for invoice in threescale.invoices.list_by_account(account):
            if invoice["state"] == InvoiceState.OPEN.value or invoice["state"] == InvoiceState.PENDING.value:
                invoice.state_update(InvoiceState.CANCELLED)

    request.addfinalizer(_cancel_invoices)
    account = custom_account(params=account)

    return account
