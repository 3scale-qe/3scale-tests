"""View representations of product's methods and metrics pages"""

from widgetastic.widget import TextInput, Table, Text, GenericLocatorWidget, View
from widgetastic_patternfly4 import Button

from testsuite.ui.navigation import step
from testsuite.ui.views.admin.product import BaseProductView
from testsuite.ui.views.common.foundation import FlashMessage
from testsuite.ui.widgets.buttons import ThreescaleCreateButton, ThreescaleDeleteButton


class ProductMethodsView(BaseProductView):
    """View representation of Product's methods page"""

    path_pattern = "/apiconfig/services/{product_id}/metrics"
    metrics_tab = GenericLocatorWidget(locator="//button[normalize-space(.)='Metrics']")
    add_method_button = Button(text="Add a method")
    methods_table = Table(
        ".//table[@data-ouia-component-id='OUIA-Generated-Table-2']", column_widgets={"Method": Text("./a")}
    )
    notification = View.nested(FlashMessage)

    @step("NewMethodView")
    def add_method(self):
        """Add new product's method"""
        self.add_method_button.click()

    @step("ProductMetricsView")
    def metrics(self):
        """Change to product's metric tab"""
        self.metrics_tab.click()

    @step("ProductMethodEditView")
    def edit(self, method):
        """Edit product's method"""
        self.methods_table.row(method=method.entity_name).method.widget.click()

    def prerequisite(self):
        return BaseProductView

    @property
    def is_displayed(self):
        return (
            BaseProductView.is_displayed.fget(self)
            and self.metrics_tab.is_displayed
            and self.add_method_button
            and self.path in self.browser.url
        )


class NewMethodView(BaseProductView):
    """View representation of new Product's method page"""

    path_pattern = "/children/new"
    name = TextInput(id="metric_friendly_name")
    system_name = TextInput(id="metric_system_name")
    create_button = ThreescaleCreateButton()

    def create(self, name, system_name):
        """Create a new product's method"""
        self.name.fill(name)
        self.system_name.fill(system_name)
        self.create_button.click()

    def prerequisite(self):
        return ProductMethodsView

    @property
    def is_displayed(self):
        return (
            BaseProductView.is_displayed.fget(self)
            and self.name.is_displayed
            and self.system_name.is_displayed
            and self.create_button.click()
            and self.path in self.browser.url
        )


class ProductMethodEditView(BaseProductView):
    """View representation of Product's method edit page"""

    path_pattern = "/apiconfig/services/{product_id}/metrics/{method_id}/edit"
    delete_button = ThreescaleDeleteButton()

    def __init__(self, parent, product, method):
        super().__init__(parent, product, method_id=method.entity_id)

    def delete(self):
        """Delete product's method"""
        self.delete_button.click()

    def prerequisite(self):
        return ProductMethodsView

    @property
    def is_displayed(self):
        return (
            BaseProductView.is_displayed.fget(self)
            and self.delete_button.is_displayed
            and self.path in self.browser.url
        )


class ProductMetricsView(BaseProductView):
    """View representation of Product's metrics page"""

    path_pattern = "/apiconfig/services/{product_id}/metrics"
    add_metric_button = Button(text="Add a metric")
    metrics_table = Table(
        ".//table[@data-ouia-component-id='OUIA-Generated-Table-2']", column_widgets={"Metric": Text("./a")}
    )
    notification = View.nested(FlashMessage)

    @step("NewMetricView")
    def add_metric(self):
        """Add new product's metric"""
        self.add_metric_button.click()

    @step("ProductMetricEditView")
    def edit(self, metric):
        """Edit product's method"""
        self.metrics_table.row(metric=metric.entity_name).metric.widget.click()

    def prerequisite(self):
        return ProductMethodsView

    @property
    def is_displayed(self):
        return (
            BaseProductView.is_displayed.fget(self)
            and self.add_metric_button.is_displayed
            and self.path in self.browser.url
        )


class NewMetricView(BaseProductView):
    """View representation of new Product's metric page"""

    path_pattern = "/children/new"
    name = TextInput(id="metric_friendly_name")
    system_name = TextInput(id="metric_system_name")
    unit = TextInput(id="metric_unit")
    create_button = ThreescaleCreateButton()

    def create(self, name, system_name, unit):
        """Create a new product's metric"""
        self.name.fill(name)
        self.system_name.fill(system_name)
        self.unit.fill(unit)
        self.create_button.click()

    def prerequisite(self):
        return ProductMethodsView

    @property
    def is_displayed(self):
        return (
            BaseProductView.is_displayed.fget(self)
            and self.name.is_displayed
            and self.system_name.is_displayed
            and self.create_button.is_displayed
            and self.path in self.browser.url
        )


class ProductMetricEditView(BaseProductView):
    """View representation of Product's metrics edit page"""

    path_pattern = "/apiconfig/services/{product_id}/metrics/{metric_id}/edit"
    delete_button = ThreescaleDeleteButton()

    def __init__(self, parent, product, metric):
        super().__init__(parent, product, metric_id=metric.entity_id)

    def delete(self):
        """Delete product's metric"""
        self.delete_button.click()

    def prerequisite(self):
        return ProductMetricsView

    @property
    def is_displayed(self):
        return (
            BaseProductView.is_displayed.fget(self)
            and self.delete_button.is_displayed
            and self.path in self.browser.url
        )
