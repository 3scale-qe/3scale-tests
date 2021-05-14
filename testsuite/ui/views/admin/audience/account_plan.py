"""View representations of Account plan pages"""
from widgetastic.widget import TextInput, GenericLocatorWidget
from widgetastic_patternfly4 import PatternflyTable

from testsuite.ui.navigation import step
from testsuite.ui.views.admin.audience import BaseAudienceView
from testsuite.ui.widgets import Link


class AccountPlansView(BaseAudienceView):
    """View representation of Account Plans Listing page"""
    path_pattern = '/buyers/account_plans'
    new_plan = Link("//a[@href='/admin/buyers/account_plans/new']")
    table = PatternflyTable("//*[@id='plans']")

    def publish(self, plan_id):
        """Publish account plan"""
        self.table.row(_row__attr=('id', f'account_plan_{plan_id}'))[3].click()

    @step("NewAccountPlanView")
    def new(self):
        """Create new account plan"""
        self.new_plan.click()

    def prerequisite(self):
        return BaseAudienceView

    @property
    def is_displayed(self):
        return BaseAudienceView.is_displayed.fget(self) and self.new_plan.is_displayed and self.table.is_displayed \
               and self.path in self.browser.url


class NewAccountPlanView(BaseAudienceView):
    """View representation of New Account page"""
    path_pattern = "/buyers/account_plans/new"
    name = TextInput(id='account_plan_name')
    system_name = TextInput(id='account_plan_system_name')
    approval = GenericLocatorWidget('//*[@id="account_plan_approval_required"]')
    trial_period = TextInput(id='account_plan_trial_period_days')
    setup_fee = TextInput(id='account_plan_setup_fee')
    cost = TextInput(id='account_plan_cost_per_month')
    create_button = GenericLocatorWidget(locator="//input[contains(@class, 'create')]")

    # pylint: disable=too-many-arguments
    @step("AccountPlansView")
    def create(self, name: str, system_name: str, approval: bool = False, trial_period: str = "", setup_fee: str = "",
               cost: str = ""):
        """Crate new accoutn plan"""
        self.name.fill(name)
        self.system_name.fill(system_name)
        if approval:
            self.approval.click()
        if trial_period:
            self.trial_period.fill(trial_period)
        if setup_fee:
            self.setup_fee.fill(setup_fee)
        if cost:
            self.cost.fill(cost)
        self.create_button.click()

    def prerequisite(self):
        return AccountPlansView

    @property
    def is_displayed(self):
        return BaseAudienceView.is_displayed.fget(self) and self.name.is_displayed and self.approval.is_displayed and \
               self.path in self.browser.url
