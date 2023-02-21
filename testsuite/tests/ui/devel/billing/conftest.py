"""Conftest for billing tests"""
import pytest
from threescale_api.resources import InvoiceState

from testsuite import rawobj
from testsuite.ui.objects import BillingAddress
from testsuite.ui.views.admin.audience.account import InvoiceDetailView
from testsuite.utils import randomize


@pytest.fixture
def line_items():
    """List of all items to be added to an invoice"""
    return [{'name': "test-item", 'description': 'test_item', 'quantity': '1', 'cost': 10}]


@pytest.fixture
def create_api_invoice(account, threescale, line_items):
    """
    Creates a new invoice via API.
    """
    def _api_invoice():
        account_invoices = threescale.invoices.list_by_account(account)
        invoice = threescale.invoices.create({"account_id": account['id']})
        for line_item in line_items:
            invoice.line_items.create(line_item)
        invoice = invoice.state_update(InvoiceState.PENDING)
        assert len(threescale.invoices.list_by_account(account)) - len(account_invoices) == 1
        return invoice

    return _api_invoice


@pytest.fixture
def create_ui_invoice(custom_admin_login, navigator, account, line_items, threescale):
    """
    Creates and charges invoice through UI.
    Asserts if a new invoice was created and charged.
    """
    def _ui_invoice():
        custom_admin_login()
        old_invoices = threescale.invoices.list_by_account(account)
        view = navigator.navigate(InvoiceDetailView, account=account)
        for line_item in line_items:
            view.add_item(**line_item)

        view.issue()
        invoice = threescale.invoices.list_by_account(account)[0]
        view.charge(invoice)
        new_invoices = threescale.invoices.list_by_account(account)
        assert len(new_invoices) - len(old_invoices) == 1
        assert view.state_field.text == "Paid"

        return new_invoices[0]

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
