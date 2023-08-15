"""APIs for Stripe and Braintree"""
import backoff
import braintree
import stripe
from braintree.exceptions.request_timeout_error import RequestTimeoutError
from braintree.exceptions.service_unavailable_error import ServiceUnavailableError

from threescale_api.resources import InvoiceState


class Stripe:
    """API for Stripe"""

    def __init__(self, api_key):
        # Due to fact that we can set up only one Stripe per 3scale and we use same api_key everytime this
        # is not disruptive even if it looks like it is.
        stripe.api_key = api_key

    @staticmethod
    def read_payment(invoice):
        """Read Stripe payment"""
        return [x for x in stripe.PaymentIntent.list() if x["metadata"]["order_id"] == str(invoice["id"])][0]

    @staticmethod
    def read_customer_by_account(account):
        """Read Stripe customer"""
        return [
            x
            for x in stripe.Customer.list()
            if str(account.entity_id) in x["metadata"].get("3scale_account_reference", [])
        ][0]

    def assert_payment(self, invoice):
        """Compare 3scale and Stripe invoices"""
        stripe_invoice = self.read_payment(invoice)
        currency = stripe_invoice["currency"]
        # Stripe amount is Integer, e.g. 10,50$ is as 1050 so we need to divide it by 100 to get wanted cost
        cost = stripe_invoice["amount"] / 100
        # Compare 3scale invoice values and Stripe invoice values and check whether Stripe invoice is marked as paid
        assert invoice["state"] == InvoiceState.PAID.value
        assert currency == invoice["currency"].lower()
        assert cost == invoice["cost"]
        assert stripe_invoice["charges"]["data"][0]["paid"]


class Braintree:
    """API for braintree"""

    def __init__(self, merchant_id, public_key, private_key):
        self.gateway = braintree.BraintreeGateway(
            braintree.Configuration(
                environment=braintree.Environment.Sandbox,
                merchant_id=merchant_id,
                public_key=public_key,
                private_key=private_key,
            )
        )

    @backoff.on_exception(backoff.fibo, (ServiceUnavailableError, RequestTimeoutError), max_tries=8, jitter=None)
    def _transaction_search(self, invoice):
        return self.gateway.transaction.search(braintree.TransactionSearch.order_id == str(invoice["id"]))

    # pylint: disable=no-member
    def merchant_currency(self):
        """Return currency code for default merchant account"""
        merchant_accounts = list(self.gateway.merchant_account.all().merchant_accounts.items)
        return [x for x in merchant_accounts if x.default is True][0].currency_iso_code

    def _assert(self, invoice):
        """Compares 3scale invoice and Braintree transaction"""
        transaction = self._transaction_search(invoice).first
        currency = transaction.currency_iso_code
        cost = float(transaction.amount)
        invoice_transaction = invoice.payment_transactions.list()[0]

        assert invoice["currency"] == currency
        assert invoice["cost"] == cost
        code, message = invoice_transaction["message"].split(" ", 1)
        assert code == transaction.processor_response_code
        assert message == transaction.processor_response_text

    def assert_payment(self, invoice):
        """
        Asserts successful payment invoice payment.
        This assert is used for transaction amount between 0.01 and 1999.9.
        """
        assert invoice["state"] == InvoiceState.PAID.value
        self._assert(invoice)

    def assert_declined_payment(self, invoice):
        """
        Asserts declined payment invoice payment.
        This assert is used for transaction amount between 2000.00 and 2999.99.
        Transaction amount of 5001, 5001.01, and 5001.02 leads to Processor Declined as well,
        but with different response codes and messages.
        """
        assert invoice["state"] == InvoiceState.PENDING.value
        self._assert(invoice)
