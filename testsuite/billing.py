"""APIs for Stripe and Braintree"""
import braintree
import stripe

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
        return [x for x in stripe.PaymentIntent.list() if x['metadata']['order_id'] == str(invoice['id'])][0]

    @staticmethod
    def read_customer_by_account(account):
        """Read Stripe customer"""
        return [x for x in stripe.Customer.list() if
                str(account.entity_id) in x["metadata"].get("3scale_account_reference", [])][0]

    def assert_payment(self, invoice):
        """Compare 3scale and Stripe invoices"""
        stripe_invoice = self.read_payment(invoice)
        currency = stripe_invoice['currency']
        # Stripe amount is Integer, e.g. 10,50$ is as 1050 so we need to divide it by 100 to get wanted cost
        cost = stripe_invoice['amount'] / 100
        # Compare 3scale invoice values and Stripe invoice values and check whether Stripe invoice is marked as paid
        assert invoice['state'] == InvoiceState.PAID.value
        assert currency == invoice['currency'].lower()
        assert cost == invoice['cost']
        assert stripe_invoice['charges']['data'][0]['paid']


# pylint: disable=too-few-public-methods
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

    # pylint: disable=no-member
    def merchant_currency(self):
        """Return currency code for default merchant account"""
        merchant_accounts = list(self.gateway.merchant_account.all().merchant_accounts.items)
        return [x for x in merchant_accounts if x.default is True][0].currency_iso_code

    def assert_payment(self, invoice):
        """Compare 3scale invoice and Braintree transaction"""
        transaction = self.gateway.transaction.search(braintree.TransactionSearch.order_id == str(invoice['id']))
        currency = transaction.first.currency_iso_code
        cost = float(transaction.first.amount)
        assert invoice['state'] == InvoiceState.PAID.value
        assert currency == invoice['currency']
        assert cost == invoice['cost']
