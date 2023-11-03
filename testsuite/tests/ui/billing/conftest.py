"""Conftest for billing tests"""
import pytest
from threescale_api.resources import InvoiceState

from testsuite import rawobj
from testsuite.ui.objects import BillingAddress
from testsuite.ui.views.admin.audience.account import InvoiceDetailView, AccountInvoicesView
from testsuite.utils import randomize


@pytest.fixture
def invoice(custom_invoice):
    """Creates a new invoice via API"""
    return custom_invoice(10)


@pytest.fixture
def custom_invoice(threescale, account):
    """
    Parametrized Invoice

    Args:
        :param cost: total invoice cost
    """

    def _custom_invoice(cost):
        account_invoices = threescale.invoices.list_by_account(account)
        invoice = threescale.invoices.create({"account_id": account["id"]})
        invoice.line_items.create({"name": "test-item", "description": "test_item", "quantity": "1", "cost": cost})
        invoice = invoice.state_update(InvoiceState.PENDING)
        assert len(threescale.invoices.list_by_account(account)) - len(account_invoices) == 1
        return invoice

    return _custom_invoice


@pytest.fixture(scope="module")
def ui_invoice(custom_admin_login, navigator, account, threescale):
    """
    Creates and charges invoice through UI.
    Asserts if a new invoice was created and charged.
    """

    def _ui_invoice():
        custom_admin_login()
        navigator.navigate(AccountInvoicesView, account=account).create()
        invoice = threescale.invoices.list_by_account(account)
        assert len(invoice) == 1, "More than one invoice was created for an Account"

        invoice_view = navigator.open(InvoiceDetailView, account=account, invoice=invoice[0])
        invoice_view.add_items([{"name": "test-item", "description": "test_item", "quantity": "1", "cost": 10}])
        invoice_view.issue()
        assert invoice_view.charge_button.wait_displayed(), "Issuing the invoice through UI failed"
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
