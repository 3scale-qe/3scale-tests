"""View representations of products application section pages"""
from widgetastic_patternfly4 import PatternflyTable

from testsuite.ui.navigation import step
from testsuite.ui.views.admin.product import BaseProductView
from testsuite.ui.widgets import GenericLocatorWidget
from testsuite.ui.widgets.buttons import ThreescaleUpdateButton


class ApplicationPlansView(BaseProductView):
    """View representation of Application plans page"""
    path_pattern = "/apiconfig/services/{product_id}/application_plans"
    table = PatternflyTable(".//*[@id='plans']")

    @step("ApplicationPlanDetailView")
    def detail(self, application_plan):
        """Detail of Application plan"""
        next(row for row in self.table.rows() if row[0].text == application_plan["name"]).name.click()

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
        return BaseProductView.is_displayed.fget(self) and self.update_btn.is_displayed\
               and self.path in self.browser.url
