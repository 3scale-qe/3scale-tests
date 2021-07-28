"""View representations of products integration configuration section pages"""
from widgetastic.widget import View, ParametrizedLocator
from widgetastic_patternfly4 import Button

from testsuite.ui.views.admin.product import BaseProductView


class ProductConfigurationView(BaseProductView):
    """View representation of Product configuration page"""
    path_pattern = "/apiconfig/services/{product_id}/integration"

    @View.nested
    # pylint: disable=invalid-name
    class configuration(View):
        """Configuration tab with promote to staging button"""
        ROOT = ParametrizedLocator('//*[@id="integration-tabs"]/div[2]/section[1]')
        staging_promote_btn = Button(locator=".//button[contains(@class,'PromoteButton')]")

    @View.nested
    # pylint: disable=invalid-name
    class staging(View):
        """Staging tab with promote to production button"""
        ROOT = ParametrizedLocator('//*[@id="integration-tabs"]/div[2]/section[2]/div[1]')
        production_promote_btn = Button(locator=".//button[contains(@class,'PromoteButton')]")

    def prerequisite(self):
        return BaseProductView

    @property
    def is_displayed(self):
        return BaseProductView.is_displayed.fget(self) and self.configuration.staging_promote_btn.is_displayed \
               and self.staging.production_promote_btn.is_displayed and self.path in self.browser.url
