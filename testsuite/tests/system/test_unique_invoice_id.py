"""
rewrite of /spec/ui_specs/billing/unique_invoice_id_spec.rb

Test automatically created invoices will not have duplicate 'friendly_id'
For testing this issue, we don't need to use UI, as all can be done trough API
"""
from datetime import date, timedelta
import pytest
from threescale_api.resources import InvoiceState, Account, ApplicationPlan
from testsuite import rawobj
from testsuite.utils import blame, blame_desc

pytestmark = [
    pytest.mark.nopersistence,
    pytest.mark.issue("https://issues.jboss.org/browse/THREESCALE-1203")
]

ACCOUNTS_COUNT = 10


@pytest.fixture()
def paid_app_plan(request, service, custom_app_plan) -> ApplicationPlan:
    """Application plan on default service with some setup fee"""
    return custom_app_plan(rawobj.ApplicationPlan(blame(request, "inv-paid"), setup_fee=100), service=service)


@pytest.fixture()
def custom_paid_account(request, paid_app_plan, custom_account, custom_application, account_password):
    """Returns function for custom account creation"""
    def _custom_paid_account(num: int) -> Account:
        """
        Makes number of accounts with applications that use paid app plan.
        :param num: Number of accounts to create
        """
        name = blame(request, f"inv-{num}")
        acc_params = rawobj.AccountUser(name, f"{name}@anything.invalid", account_password)
        acc_params.update(org_name=name)
        account = custom_account(acc_params)
        custom_application(rawobj.Application(name, paid_app_plan, blame_desc(request, "desc")), account=account)
        return account
    return _custom_paid_account


@pytest.fixture()
def create_invoice(custom_paid_account, master_threescale, threescale,
                   provider_account, request):
    """Creates ACCOUNTS_COUNT accounts and for each account charge invoice with master_api"""
    next_day = (date.today() + timedelta(days=1)).isoformat()
    accounts = []
    for i in range(ACCOUNTS_COUNT):
        account = custom_paid_account(i)
        accounts.append(account)
        master_threescale.tenants.trigger_billing_account(provider_account, account, next_day)

    def clean_invoice():
        for acc in accounts:
            for invoice in threescale.invoices.list_by_account(acc):
                invoice.state_update(InvoiceState.CANCELLED)

    request.addfinalizer(clean_invoice)

    return accounts


def test_unique_invoice(create_invoice, threescale):  # pylint: disable=unused-argument
    """For all accounts combined (ACCOUNTS_COUNT times created) check if there are no duplicate 'friendly_id'"""
    invoices = []
    invoices_by_friendly_id = set()  # duplicates gets squashed
    for acc in create_invoice:
        for invoice in threescale.invoices.list_by_account(acc):
            invoices.append(invoice)
            invoices_by_friendly_id.add(invoice['friendly_id'])

    assert len(invoices) == len(invoices_by_friendly_id) == ACCOUNTS_COUNT
