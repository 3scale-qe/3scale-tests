"""Tests simple billing using both API and UI"""

import pytest
from threescale_api.resources import InvoiceState

from testsuite import rawobj
from testsuite.ui.objects import CreditCard
from testsuite.ui.views.devel.settings.stripe import StripeCCView
from testsuite.utils import randomize


@pytest.fixture(scope="module", params=[
    pytest.param(("4000002500003155", True)),
    pytest.param(("4242424242424242", False)),
])
def cc_details(request):
    """Credit card details"""
    return CreditCard(request.param[0], 123, 10, 25, request.param[1])


@pytest.fixture(scope="function")
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


@pytest.mark.parametrize("invoice_provider", [
    "api_invoice",
    "ui_invoice"
])
# pylint: disable=too-many-arguments,unused-argument
def test_stripe(devel_login, navigator, billing_address, cc_details, request, account, threescale, invoice_provider):
    """Tests stripe billing"""
    cc_view = navigator.navigate(StripeCCView)
    cc_view.add_cc_details(billing_address, cc_details)

    request.getfixturevalue(invoice_provider)
    acc_invoices = threescale.invoices.list_by_account(account)
    assert len(acc_invoices) == 1
    assert acc_invoices[0]['state'] == InvoiceState.PAID.value
    # TODO: Stripe asserts
