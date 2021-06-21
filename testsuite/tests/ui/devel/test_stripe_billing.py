import time

import pytest
import requests
from threescale_api.resources import InvoiceState

from testsuite.tests.ui import CreditCard
from testsuite.ui.views.devel.settings.stripe import StripeCCView


@pytest.fixture(scope="module")
def cc_details():
    return CreditCard("4000002500003155", "123", 10, 25)


@pytest.fixture
def invoice(account, threescale):
    new_invoice = threescale.invoices.create(dict(account_id=account['id']))
    new_invoice.line_items.create(dict(name="test-item",
                                       description='test_item',
                                       quantity='1',
                                       cost=10))
    return new_invoice


def test_stripe(devel_login, navigator, billing_address, cc_details, account, invoice, threescale):
    cc_view = navigator.navigate(StripeCCView)
    cc_view.add_cc_details(billing_address, cc_details, otp=True)
    invoice.state_update(InvoiceState.pending)
    id = invoice.entity_id
    a = {'access_token': 'dde10348f2eb7f9b54448a28a29f779a2f8a82b611936e19d72b505d603c5c7f'}
    responce = requests.post(f"https://3scale-admin.ga.apps.ocp.api-qe.eng.rdu2.redhat.com/api/invoices/{id}/charge.xml", data=a)
    # invoice.charge()
    acc_invoices = threescale.invoices.list_by_account(account)
    assert len(acc_invoices) == 1
    assert acc_invoices[0]['state'] == InvoiceState.paid.name
    # assert
