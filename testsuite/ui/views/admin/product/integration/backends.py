"""View representations of products integration backends section pages"""
from widgetastic.widget import TextInput
from widgetastic_patternfly4 import PatternflyTable

from testsuite.ui.navigation import step
from testsuite.ui.views.admin.product import BaseProductView
from testsuite.ui.widgets import Link, GenericLocatorWidget, ThreescaleDropdown
from testsuite.ui.widgets.buttons import ThreescaleCreateButton


class ProductBackendsView(BaseProductView):
    """View representation of Product's Backends page"""
    path_pattern = "/apiconfig/services/{product_id}/backend_usages"
    add_backend_button = Link("//*[contains(@href,'/backend_usages/new')]")
    backend_table = PatternflyTable("//*[@id='backend_api_configs']", column_widgets={
        "Add Backend": GenericLocatorWidget("./a[contains(@class, 'delete')]")})

    @step("ProductAddBackendView")
    def add_backend(self):
        """Add backend"""
        self.add_backend_button.click()

    def remove_backend(self, backend):
        """Remove backend"""
        next(row for row in self.backend_table.rows() if row[0].text == backend["name"])[3].widget.click(True)

    def prerequisite(self):
        return BaseProductView

    @property
    def is_displayed(self):
        return BaseProductView.is_displayed.fget(self) and self.path in self.browser.url and \
               self.backend_table.is_displayed


class ProductAddBackendView(BaseProductView):
    """View representation of Product's Backends add page"""
    path_pattern = "/apiconfig/services/{product_id}/backend_usages/new"
    backend = ThreescaleDropdown("//*[id='backend_api_config_backend_api_id']")
    backend_path = TextInput(id="backend_api_config_path")
    add_button = ThreescaleCreateButton()

    def add_backend(self, backend, path):
        """Add backend"""
        self.backend.select_by_value(backend.entity_id)
        self.backend_path.fill(path)
        self.add_button.click()

    def prerequisite(self):
        return ProductBackendsView

    @property
    def is_displayed(self):
        return BaseProductView.is_displayed.fget(self) and self.path in self.browser.url \
               and self.backend.is_displayed and self.backend_path.is_displayed
