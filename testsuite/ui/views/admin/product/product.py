"""View representations of Product pages"""
from widgetastic.widget import TextInput, Text

from testsuite.ui.navigation import step
from testsuite.ui.views.admin.foundation import BaseAdminView
from testsuite.ui.views.admin.product import BaseProductView, ProductsView
from testsuite.ui.widgets.buttons import ThreescaleCreateButton, ThreescaleUpdateButton, ThreescaleDeleteButton


class ProductNewView(BaseAdminView):
    """View representation of New Product page"""
    path_pattern = "/apiconfig/services/new"
    name = TextInput(id="service_name")
    system_name = TextInput(id="service_system_name")
    description = TextInput(id="service_description")
    create_button = ThreescaleCreateButton()

    def create(self, name: str, system: str, desc: str):
        """Create Product"""
        self.name.fill(name)
        self.system_name.fill(system)
        self.description.fill(desc)
        self.create_button.click()

    def prerequisite(self):
        return ProductsView

    @property
    def is_displayed(self):
        return BaseAdminView.is_displayed.fget(self) and self.path in self.browser.url \
               and self.name.is_displayed and self.system_name.is_displayed


class ProductDetailView(BaseProductView):
    """View representation of Product detail page (Overview page)"""
    path_pattern = "/apiconfig/services/{product_id}"
    edit_button = Text(locator="//*[@id='content']/section/div/a")

    @step("ProductEditView")
    def edit(self):
        """Edit Product"""
        self.edit_button.click()

    def prerequisite(self):
        return BaseProductView

    @property
    def is_displayed(self):
        return BaseProductView.is_displayed.fget(self) and self.path in self.browser.url \
               and self.edit_button.is_displayed


class ProductEditView(BaseProductView):
    """View representation of Edit Product page"""
    path_pattern = "/apiconfig/services/{product_id}/edit"
    name = TextInput(id="service_name")
    description = TextInput(id="service_description")
    update_button = ThreescaleUpdateButton()
    delete_button = ThreescaleDeleteButton()

    def update(self, name: str = "", desc: str = ""):
        """Update Product"""
        if name:
            self.name.fill(name)
        if desc:
            self.description.fill(desc)

        self.update_button.click()

    def delete(self):
        """Delete Product"""
        self.delete_button.click()

    def prerequisite(self):
        return ProductDetailView

    @property
    def is_displayed(self):
        return BaseProductView.is_displayed.fget(self) and self.path in self.browser.url \
               and self.name.is_displayed and self.description.is_displayed
