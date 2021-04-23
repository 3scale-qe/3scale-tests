"""View representations of Product pages"""
from widgetastic.widget import TextInput, GenericLocatorWidget
from widgetastic_patternfly4 import PatternflyTable

from testsuite.ui.navigation import step
from testsuite.ui.views.admin.foundation import ProductNavView, ProductsView, BaseAdminView
from testsuite.ui.widgets import Link, ThreescaleDropdown, DeploymentRadio
from testsuite.ui.widgets.buttons import ThreescaleCreateButton, ThreescaleUpdateButton, ThreescaleDeleteButton


class ProductDetailView(ProductNavView):
    """View representation of Product detail page"""
    endpoint_path = "/apiconfig/services/{product_id}"
    edit_button = Link(locator="//*[@id='content']/section/div/a")
    configuration_outdated = GenericLocatorWidget("//*[contains(@href, '/integration')]")

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


class ProductSettingsView(ProductNavView):
    """View representation of Product's Settings page"""
    endpoint_path = "/apiconfig/services/{product_id}/settings"
    staging_url = TextInput(id="service_proxy_attributes_sandbox_endpoint")
    production_url = TextInput(id="service_proxy_attributes_endpoint")
    deployment = DeploymentRadio('//*[@id="service_deployment_option_input"]')
    update_button = ThreescaleUpdateButton()

    def prerequisite(self):
        return ProductDetailView

    @property
    def is_displayed(self):
        return ProductNavView.is_displayed and self.endpoint_path in self.browser.url \
               and self.deployment.is_displayed

    def update_gateway(self, staging="", production=""):
        """Update gateway"""
        if staging:
            self.staging_url.fill(staging)
        if production:
            self.production_url.fill(production)
        self.update_button.click()

    def change_deployment(self, option):
        """Change deployment"""
        self.deployment.select([option])
        self.update_button.click()


class ProductBackendsView(ProductNavView):
    """View representation of Product's Backends page"""
    endpoint_path = "/apiconfig/services/{product_id}/backend_usages"
    add_backend_button = Link("//*[contains(@href,'/backend_usages/new')]")
    backend_table = PatternflyTable("//*[@id='backend_api_configs']", column_widgets={
        "Add Backend": GenericLocatorWidget("./a[contains(@class, 'delete')]")
    })

    def prerequisite(self):
        return ProductDetailView

    @property
    def is_displayed(self):
        return ProductNavView.is_displayed and self.endpoint_path in self.browser.url \
               and self.backend_table.is_displayed

    @step("ProductAddBackendView")
    def add_backend(self):
        """Add backend"""
        self.add_backend_button.click()

    def remove_backend(self, backend):
        """Remove backend"""
        next(row for row in self.backend_table.rows() if row[0].text == backend["name"])[3].widget.click(True)


class ProductAddBackendView(ProductNavView):
    """View representation of Product's Backends add page"""
    endpoint_path = "/apiconfig/services/{product_id}/backend_usages/new"
    backend = ThreescaleDropdown("//*[id='backend_api_config_backend_api_id']")
    path = TextInput(id="backend_api_config_path")
    add_button = ThreescaleCreateButton()

    def prerequisite(self):
        return ProductBackendsView

    @property
    def is_displayed(self):
        return ProductNavView.is_displayed and self.endpoint_path in self.browser.url \
               and self.backend.is_displayed and self.path.is_displayed

    def add_backend(self, backend, path):
        """Add backend"""
        self.backend.select_by_value(backend.entity_id)
        self.path.fill(path)
        self.add_button.click()


class ProductConfigurationView(ProductNavView):
    """View representation of Product configuration page"""
    endpoint_path = "/apiconfig/services/{product_id}/integration"

    def prerequisite(self):
        return ProductDetailView

    @property
    def is_displayed(self):
        return ProductNavView.is_displayed and self.endpoint_path in self.browser.url


class ApplicationPlansView(ProductNavView):
    """View representation of Application plans page"""
    endpoint_path = "/apiconfig/services/{product_id}/application_plans"
    table = PatternflyTable(".//*[@id='plans']")

    def prerequisite(self):
        return ProductDetailView

    @property
    def is_displayed(self):
        return ProductNavView.is_displayed and self.endpoint_path in self.browser.url \
               and self.table.is_displayed

    @step("ApplicationPlanDetailView")
    def detail(self, application_plan):
        """Detail of Application plan"""
        next(row for row in self.table.rows() if row[0].text == application_plan["name"]).name.click()


class ApplicationPlanDetailView(ProductNavView):
    """View representation of Application plan detail page"""
    endpoint_path = "/apiconfig/application_plans/{application_plan_id}/edit"
    product_level = PatternflyTable(".//*[@id='metrics']")

    def prerequisite(self):
        return ApplicationPlansView

    @property
    def is_displayed(self):
        return ProductNavView.is_displayed and self.endpoint_path in self.browser.url
