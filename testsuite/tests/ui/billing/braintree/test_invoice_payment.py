"""Braintree gateway billing tests"""
import pytest


pytestmark = [
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-7762"),
]


@pytest.fixture(scope="module", autouse=True)
def card_setup(custom_card):
    """Card setup"""
    custom_card("4111111111111111")


def normalize_url(url):
    """Invoice url need to be changed from internal to external form"""
    for rep in (("3scale-admin", "3scale"), ("/api/", "/admin/account/")):
        url = url.replace(*rep)
    return url


def test_no_sca_ui_invoice(braintree, ui_invoice, account):
    """Tests basic billing scenario for Braintree gateway where billing is triggered via UI"""
    invoice_view = ui_invoice()
    transaction = braintree.ensure_single_transaction(invoice_view.charge, account)
    braintree.assert_payment(invoice_view.invoice.read(), transaction)
    assert invoice_view.state_field.text == "State Paid"


def test_mail_completed_payment(invoice, mailhog_client):
    """Tests mail notification about successful payment"""
    invoice.charge()
    mailhog_client.assert_message_received(
        subject="Provider Name API - Payment completed",
        content=f"successfully completed your monthly payment for our service of USD {invoice.entity['cost']}0.\r\n\r\n"
        f"Your invoice is available online at:\r\n\r\n{normalize_url(invoice.url)}",
    )
