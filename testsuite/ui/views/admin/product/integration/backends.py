"""View representations of products integration backends section pages"""

from widgetastic.widget import Text, TextInput
from widgetastic_patternfly4 import Button, PatternflyTable
from widgetastic_patternfly4.ouia import Select

from testsuite.ui.navigation import step
from testsuite.ui.views.admin.product import BaseProductView
from testsuite.ui.widgets import GenericLocatorWidget


class ProductBackendsView(BaseProductView):
    """View representation of Product's Backends page"""

    path_pattern = "/apiconfig/services/{product_id}/backend_usages"
    add_backend_button = Text("//*[contains(@href,'/backend_usages/new')]")
    backend_table = PatternflyTable(
        "//table[@aria-label='Backends table']",
        column_widgets={3: GenericLocatorWidget("//div/a[contains(@class, 'delete')]")},
    )

    @step("ProductAddBackendView")
    def add_backend(self):
        """Add backend"""
        self.add_backend_button.click()

    def remove_backend(self, backend):
        """Remove backend"""
        self.backend_table.row(name__contains=backend["name"])[3].widget.click(True)

    def prerequisite(self):
        return BaseProductView

    @property
    def is_displayed(self):
        return (
            BaseProductView.is_displayed.fget(self)
            and self.path in self.browser.url
            and self.backend_table.is_displayed
        )


class ProductAddBackendView(BaseProductView):
    """View representation of Product's Backends add page"""

    path_pattern = "/apiconfig/services/{product_id}/backend_usages/new"
    backend = Select(component_id="Backend")
    backend_path = TextInput(id="backend_api_config_path")
    add_button = Button(locator="//*[@data-testid='addBackend-buttonSubmit']")

    def add_backend(self, backend, path):
        """Add backend"""
        self.backend.item_select(backend.entity_name)
        self.backend_path.fill(path)
        self.add_button.click()

    def prerequisite(self):
        return ProductBackendsView

    @property
    def is_displayed(self):
        return (
            BaseProductView.is_displayed.fget(self)
            and self.path in self.browser.url
            and self.backend.is_displayed
            and self.backend_path.is_displayed
        )
