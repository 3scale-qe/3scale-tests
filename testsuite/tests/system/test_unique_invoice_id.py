"""
rewrite of /spec/ui_specs/billing/unique_invoice_id_spec.rb

Test automatically created invoices will not have duplicate 'friendly_id'
For testing this issue, we don't need to use UI, as all can be done trough API
"""
from datetime import date, timedelta
import backoff
import pytest
from threescale_api.resources import InvoiceState, Account, ApplicationPlan
from testsuite import rawobj

pytestmark = [
    pytest.mark.nopersistence,
    pytest.mark.issue("https://issues.jboss.org/browse/THREESCALE-1203")
]

ACCOUNTS_COUNT = 10


@pytest.fixture()
def paid_app_plan(service, custom_app_plan) -> ApplicationPlan:
    """Application plan on default service with some setup fee"""
    return custom_app_plan(rawobj.ApplicationPlan("paidplan", setup_fee=100), service=service)


@pytest.fixture()
def custom_paid_account(paid_app_plan, custom_account, custom_application, account_password):
    """Returns function for custom account creation"""
    def _custom_paid_account(num: int) -> Account:
        """
        Makes number of accounts with applications that use paid app plan.
        :param num: Number of accounts to create
        """
        acc_params = rawobj.AccountUser(f"test-{num}", f"{num}@anything.invalid", account_password)
        acc_params.update(org_name=f"test-{num}")
        account = custom_account(acc_params)
        custom_application(rawobj.Application(f"app-{num})", paid_app_plan, "desc"), account=account)
        return account
    return _custom_paid_account


@pytest.fixture()
def create_invoice(custom_paid_account, master_threescale, threescale,
                   provider_account, request):
    """Creates ACCOUNTS_COUNT accounts and for each account charge invoice with master_api"""
    def clean_invoice():
        for i in range(ACCOUNTS_COUNT):
            acc: Account = threescale.accounts.read_by_name(f"test-{i}")
            for invoice in threescale.invoices.list_by_account(acc):
                invoice.state_update(InvoiceState.CANCELLED)

    request.addfinalizer(clean_invoice)

    next_day = (date.today() + timedelta(days=1)).isoformat()

    for i in range(ACCOUNTS_COUNT):
        account = custom_paid_account(i)
        master_threescale.tenants.trigger_billing_account(provider_account, account, next_day)


# this is flaky little bit, not all the invoices seem triggered instantly
@backoff.on_exception(backoff.fibo, AssertionError, max_tries=8, jitter=None)
def test_unique_invoice(create_invoice, threescale):  # pylint: disable=unused-argument
    """For all accounts combined (ACCOUNTS_COUNT times created) check if there are no duplicate 'friendly_id'"""
    invoices = []
    invoices_by_friendly_id = set()  # duplicates gets squashed
    for i in range(ACCOUNTS_COUNT):
        acc: Account = threescale.accounts.read_by_name(f"test-{i}")
        for invoice in threescale.invoices.list_by_account(acc):
            invoices.append(invoice)
            invoices_by_friendly_id.add(invoice['friendly_id'])

    assert len(invoices) == len(invoices_by_friendly_id) == ACCOUNTS_COUNT
