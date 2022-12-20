"""View representations of products application section pages"""
from widgetastic.widget import Text, TextInput, View
from widgetastic_patternfly4 import PatternflyTable, Select

from testsuite.ui.navigation import step
from testsuite.ui.views.admin.product import BaseProductView
from testsuite.ui.widgets import GenericLocatorWidget
from testsuite.ui.widgets.buttons import ThreescaleUpdateButton, ThreescaleCreateButton, ThreescaleSubmitButton
from testsuite.ui.views.common.foundation import FlashMessage


class ApplicationPlansView(BaseProductView):
    """View representation of Application plans page"""
    path_pattern = "/apiconfig/services/{product_id}/application_plans"
    table = PatternflyTable(".//*[@aria-label='Plans Table']", column_widgets={
        "Name": Text("./a")
    })
    create_button = ThreescaleCreateButton()
    change_plan_button = ThreescaleSubmitButton()
    default_plan_select = Select()
    notification = View.nested(FlashMessage)

    def change_default_plan(self, plan_name: str):
        """
        Change default application plan
        plan_name: Name of application plan
        """
        self.default_plan_select.item_select(plan_name)
        if self.change_plan_button.is_enabled:
            self.change_plan_button.click()
        else:
            raise ValueError("Change button is not enabled")

    @step("ApplicationPlanDetailView")
    def detail(self, application_plan):
        """Detail of Application plan"""
        self.table.row(name__contains=application_plan["name"]).name.widget.click()

    @step("ApplicationPlanNewView")
    def create(self):
        """Create new Application plan"""
        self.create_button.click()

    def prerequisite(self):
        return BaseProductView

    @property
    def is_displayed(self):
        return BaseProductView.is_displayed.fget(self) and self.path in self.browser.url \
               and self.table.is_displayed


class ApplicationPlanDetailView(BaseProductView):
    """View representation of Application plan detail page"""
    path_pattern = "/apiconfig/application_plans/{application_plan_id}/edit"
    product_level = PatternflyTable(".//*[@id='metrics']")

    def __init__(self, parent, product, application_plan):
        super().__init__(parent, product, application_plan_id=application_plan.entity_id)

    def prerequisite(self):
        return ApplicationPlansView

    @property
    def is_displayed(self):
        return BaseProductView.is_displayed.fget(self) and self.product_level.is_displayed \
               and self.path in self.browser.url


class UsageRulesView(BaseProductView):
    """View representation of Product's application usage rules page"""
    path_pattern = "/apiconfig/services/{product_id}/usage_rules"
    referrer_filtering_checkbox = GenericLocatorWidget("#service_referrer_filters_required")
    update_btn = ThreescaleUpdateButton()

    def update_usage_rules(self):
        """Update usage rules"""
        self.update_btn.click()

    def prerequisite(self):
        return BaseProductView

    @property
    def is_displayed(self):
        return BaseProductView.is_displayed.fget(self) and self.update_btn.is_displayed \
               and self.path in self.browser.url


class ApplicationPlanNewView(BaseProductView):
    """View representation of New Application Plan page"""
    path_pattern = "/apiconfig/services/{product_id}/application_plans/new"
    name = TextInput(id="application_plan_name")
    system_name = TextInput(id="application_plan_system_name")
    create_button = ThreescaleCreateButton()

    def create(self, name: str, system_name: str):
        """Create application plan"""
        self.name.fill(name)
        self.system_name.fill(system_name)
        self.create_button.click()

    def prerequisite(self):
        return ApplicationPlansView

    @property
    def is_displayed(self):
        return BaseProductView.is_displayed.fget(self) and self.create_button.is_displayed and self.name.is_displayed \
               and self.system_name.is_displayed and self.path in self.browser.url
