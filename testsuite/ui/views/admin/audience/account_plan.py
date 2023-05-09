"""View representations of Account plan pages"""
from widgetastic.widget import TextInput, GenericLocatorWidget, Text
from widgetastic_patternfly4 import PatternflyTable, Dropdown

from testsuite.ui.navigation import step
from testsuite.ui.views.admin.audience import BaseAudienceView
from testsuite.ui.widgets.buttons import ThreescaleSubmitButton


class AccountPlansView(BaseAudienceView):
    """View representation of Account Plans Listing page"""

    path_pattern = "/buyers/account_plans"
    new_plan = Text("//a[@href='/admin/buyers/account_plans/new']")
    table = PatternflyTable(
        "//*[@data-ouia-component-id='OUIA-Generated-Table-2']",
        column_widgets={
            3: Dropdown(""),
        },
    )

    def publish(self, plan_name):
        """Publish account plan"""
        self.table.row(name=plan_name)[3].widget.item_select("Publish")

    @step("NewAccountPlanView")
    def new(self):
        """Create new account plan"""
        self.new_plan.click()

    def prerequisite(self):
        return BaseAudienceView

    @property
    def is_displayed(self):
        return (
            BaseAudienceView.is_displayed.fget(self)
            and self.new_plan.is_displayed
            and self.table.is_displayed
            and self.path in self.browser.url
        )


class NewAccountPlanView(BaseAudienceView):
    """View representation of New Account page"""

    path_pattern = "/buyers/account_plans/new"
    name = TextInput(id="account_plan_name")
    system_name = TextInput(id="account_plan_system_name")
    approval = GenericLocatorWidget('//*[@id="account_plan_approval_required"]')
    trial_period = TextInput(id="account_plan_trial_period_days")
    setup_fee = TextInput(id="account_plan_setup_fee")
    cost = TextInput(id="account_plan_cost_per_month")
    create_button = ThreescaleSubmitButton()

    # pylint: disable=too-many-arguments
    @step("AccountPlansView")
    def create(
        self,
        name: str,
        system_name: str,
        approval: bool = False,
        trial_period: str = "",
        setup_fee: str = "",
        cost: str = "",
    ):
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
        return (
            BaseAudienceView.is_displayed.fget(self)
            and self.name.is_displayed
            and self.approval.is_displayed
            and self.path in self.browser.url
        )
