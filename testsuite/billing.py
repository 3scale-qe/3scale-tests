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
    @backoff.on_predicate(backoff.fibo, lambda x: x == [], max_tries=10, jitter=None)
    def read_charge(customer):
        """Retrieves the details of the charge"""
        return stripe.Charge.search(query=f"customer:'{customer['id']}'").get("data")

    @staticmethod
    @backoff.on_exception(backoff.expo, IndexError, max_tries=4, jitter=None)
    def read_customer_by_account(account):
        """
        Read Stripe customer.
        Different 3scale deployments can have customers with the same id, which is reflected to the
        `3scale_account_reference` Stripe Customer variable. This method reads just the last one.
        """
        return stripe.Customer.search(
            query=f"metadata['3scale_account_reference']:'3scale-2-{str(account.entity_id)}'"
        ).get("data")[0]

    def assert_payment(self, invoice, account):
        """Compare 3scale and Stripe invoices"""
        customer = self.read_customer_by_account(account)
        charge = self.read_charge(customer)[0]

        assert charge["customer"] == customer["id"]
        assert charge["paid"]

        assert invoice["state"] == InvoiceState.PAID.value
        assert invoice["currency"].lower() == charge["currency"]
        assert invoice["cost"] == charge["amount"] / 100  # Stripe stores the cost without decimal point: 10,50$ is 1050


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
    def get_customer_transactions(self, account):
        """Finds all transactions for account"""
        transactions = list(
            self.gateway.transaction.search(braintree.TransactionSearch.customer_id == self.customer_id(account)).items
        )

        return transactions

    # pylint: disable=no-member
    def merchant_currency(self):
        """Return currency code for default merchant account"""
        merchant_accounts = list(self.gateway.merchant_account.all().merchant_accounts.items)
        return [x for x in merchant_accounts if x.default is True][0].currency_iso_code

    @staticmethod
    def customer_id(account):
        """Returns Braintree customer id. It is in a form `3scale-2-{account_id}-1`"""
        return f"3scale-2-{account.entity_id}-1"

    @staticmethod
    def _assert_transaction(invoice, transaction):
        """Compares 3scale invoice and Braintree transaction"""
        currency = transaction.currency_iso_code
        cost = float(transaction.amount)
        invoice_transaction = invoice.payment_transactions.list()[0]

        assert invoice["currency"] == currency
        assert invoice["cost"] == cost
        code, message = invoice_transaction["message"].split(" ", 1)
        assert code == transaction.processor_response_code
        assert message == transaction.processor_response_text

    def ensure_single_transaction(self, charge, account):
        """
        Counts number of transactions for account before and after charging the invoice.

        Args:
            :param charge: method reference that charges the invoice
            :param account: account that invoice will be charged for
        """
        old = self.get_customer_transactions(account)
        charge()
        new = self.get_customer_transactions(account)
        assert len(new) == len(old) + 1

        return new[0]

    def assert_payment(self, invoice, transaction):
        """
        Asserts successful payment invoice payment.
        This assert is used for transaction amount between 0.01 and 1999.9.
        """
        assert invoice["state"] == InvoiceState.PAID.value
        self._assert_transaction(invoice, transaction)

    def assert_declined_payment(self, invoice, transaction):
        """
        Asserts declined payment invoice payment.
        This assert is used for transaction amount between 2000.00 and 2999.99.
        Transaction amount of 5001, 5001.01, and 5001.02 leads to Processor Declined as well,
        but with different response codes and messages.
        """
        assert invoice["state"] == InvoiceState.PENDING.value
        self._assert_transaction(invoice, transaction)
