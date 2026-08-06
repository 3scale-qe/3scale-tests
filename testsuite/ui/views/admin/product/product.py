"""View representations of Product pages"""

from widgetastic.widget import (
    ConditionalSwitchableView,
    GenericLocatorWidget,
    TextInput,
    View,
)
from widgetastic_patternfly4 import Button

from testsuite.ui.navigation import step
from testsuite.ui.views.admin.foundation import BaseAdminView
from testsuite.ui.views.admin.product import BaseProductView, ProductsView
from testsuite.ui.widgets import RadioGroup, ThreescaleDropdown
from testsuite.ui.widgets.buttons import (
    ThreescaleCreateButton,
    ThreescaleDeleteButton,
    ThreescaleUpdateButton,
)


class ProductNewView(BaseAdminView):
    """View representation of New Product page"""

    path_pattern = "/apiconfig/services/new"
    product_radio = RadioGroup('//*[@id="new_service_source"]')
    product = ConditionalSwitchableView(reference="product_radio")
    create_button = ThreescaleCreateButton()

    # pylint: disable=undefined-variable
    @product.register(condition=lambda product_radio: product_radio == "source_manual")
    class CreateProduct(View):
        """View for creation of new product"""

        name = TextInput(id="service_name")
        system_name = TextInput(id="service_system_name")
        description = TextInput(id="service_description")

        @property
        def is_displayed(self):
            return self.name.is_displayed and self.system_name.is_displayed

    # pylint: disable=undefined-variable
    @product.register(condition=lambda product_radio: product_radio == "source_discover")
    class ImportProduct(View):
        """View for import of new product"""

        loading = GenericLocatorWidget('//*[contains(@class, "fa-spin")]')
        namespace = ThreescaleDropdown('//*[@id="service_namespace"]/..')
        name = ThreescaleDropdown('//*[@id="service_name"]/..')

        @property
        def is_displayed(self):
            return self.name.is_enabled and self.namespace.is_enabled and not self.loading.is_displayed

    def create(self, name: str, system: str, desc: str):
        """Create Product"""
        self.product.name.fill(name)
        self.product.system_name.fill(system)
        self.product.description.fill(desc)
        self.create_button.click()

    def discover(self):
        """Import product from OpenShift"""
        self.product_radio.select("source_discover")
        self.product.wait_displayed()
        self.create_button.click()

    def prerequisite(self):
        return ProductsView

    @property
    def is_displayed(self):
        return BaseAdminView.is_displayed.fget(self) and self.path in self.browser.url and self.product.is_displayed


class ProductDetailView(BaseProductView):
    """View representation of Product detail page (Overview page)"""

    path_pattern = "/apiconfig/services/{product_id}"
    ROOT = ".//main[@id='content']"
    edit_button = Button("edit")

    @step("ProductEditView")
    def edit(self):
        """Edit Product"""
        self.edit_button.click()

    def prerequisite(self):
        return BaseProductView

    @property
    def is_displayed(self):
        return (
            BaseProductView.is_displayed.fget(self) and self.path in self.browser.url and self.edit_button.is_displayed
        )


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
        return (
            BaseProductView.is_displayed.fget(self)
            and self.path in self.browser.url
            and self.name.is_displayed
            and self.description.is_displayed
        )
