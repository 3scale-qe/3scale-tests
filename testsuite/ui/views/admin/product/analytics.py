"""View representations of Product Analytics pages"""

from testsuite.ui.views.admin.product import BaseProductView
from testsuite.ui.widgets import ThreescaleAnalyticsDropdown


class ProductTrafficView(BaseProductView):
    """View representation of Analytics page"""

    path_pattern = "/services/{product_id}/stats/usage"
    traffic_dropdown = ThreescaleAnalyticsDropdown(locator="//button[contains(@class,'StatsSelector-item')]")

    def select_metric(self, value):
        """Select specific hits"""
        self.traffic_dropdown.select(value)

    def read_metric(self):
        """Read specific metric and parse it to integer"""
        return int(self.traffic_dropdown.text().split(" ")[0])

    def prerequisite(self):
        return BaseProductView

    @property
    def is_displayed(self):
        return (
            BaseProductView.is_displayed.fget(self)
            and self.path in self.browser.url
            and self.traffic_dropdown.is_displayed
        )
