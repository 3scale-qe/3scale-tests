"""View representations of Product pages"""
from widgetastic.widget import TextInput

from testsuite.ui.navigation import step
from testsuite.ui.views.admin.foundation import ProductNavView, ProductsView, BaseAdminView
from testsuite.ui.widgets import Link
from testsuite.ui.widgets.buttons import ThreescaleUpdateButton, ThreescaleDeleteButton, \
    ThreescaleCreateButton


class ProductDetailView(ProductNavView):
    """View representation of Product detail page"""
    endpoint_path = "/apiconfig/services/{product_id}"
    edit_button = Link(locator="//*[@id='content']/section/div/a")

    def prerequisite(self):
        return ProductsView

    @property
    def is_displayed(self):
        return ProductNavView.is_displayed and self.endpoint_path in self.browser.url and self.edit_button.is_displayed

    @step("ProductEditView")
    def edit(self):
        """Edit Product"""
        self.edit_button.click()


class ProductNewView(BaseAdminView):
    """View representation of New Product page"""
    endpoint_path = "/apiconfig/services/new"
    name = TextInput(id="service_name")
    system_name = TextInput(id="service_system_name")
    description = TextInput(id="service_description")
    create_button = ThreescaleCreateButton()

    def prerequisite(self):
        return ProductsView

    @property
    def is_displayed(self):
        return ProductNavView.is_displayed and self.endpoint_path in self.browser.url \
               and self.name.is_displayed and self.system_name.is_displayed

    def create(self, name: str, system: str, desc: str):
        """Create Product"""
        self.name.fill(name)
        self.system_name.fill(system)
        self.description.fill(desc)
        self.create_button.click()


class ProductEditView(ProductNavView):
    """View representation of Edit Product page"""
    endpoint_path = "/apiconfig/services/{product_id}/edit"
    name = TextInput(id="service_name")
    description = TextInput(id="service_description")
    update_button = ThreescaleUpdateButton()
    delete_button = ThreescaleDeleteButton()

    def prerequisite(self):
        return ProductDetailView

    @property
    def is_displayed(self):
        return ProductNavView.is_displayed and self.endpoint_path in self.browser.url \
               and self.name.is_displayed and self.description.is_displayed

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
