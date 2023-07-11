"""Essential Views for Product Views"""
from widgetastic.widget import GenericLocatorWidget, Text
from widgetastic_patternfly4 import PatternflyTable

from testsuite.ui.navigation import step
from testsuite.ui.views.admin.foundation import BaseAdminView
from testsuite.ui.widgets.ouia import Navigation
from testsuite.ui.widgets.searchinput import ThreescaleSearchInput


class ProductsView(BaseAdminView):
    """View representation of Product Listing page"""

    path_pattern = "/apiconfig/services"
    create_product_button = Text("//a[@href='/apiconfig/services/new']")
    table = PatternflyTable("//*[@id='products']/section/table", column_widgets={"Name": Text("./a")})
    search_input = ThreescaleSearchInput()

    def search(self, value: str):
        """Search in product table by given value"""
        self.search_input.fill_and_search(value)

    @step("BaseProductView")
    def detail(self, product):
        """Detail of Product"""
        self.table.row(system_name__contains=product.entity_name).name.widget.click()

    @step("ProductNewView")
    def create_product(self):
        """Create new Product"""
        self.create_product_button.click()

    def prerequisite(self):
        return BaseAdminView

    @property
    def is_displayed(self):
        return self.path in self.browser.url and self.table.is_displayed and BaseAdminView.is_displayed.fget(self)


class BaseProductView(BaseAdminView):
    """
    Parent View for Product Views. Navigation menu for Product Views contains title with system_name of currently
    displayed Product (this applies for all Views that inherits from BaseProductView).
    This value is verified in `is_displayed` method.
    """

    NAV_ITEMS = ["Overview", "Analytics", "Applications", "ActiveDocs", "Integration"]
    nav = Navigation()
    outdated_config = GenericLocatorWidget(locator="//*/li/a[contains(@class, 'outdated-config')]")

    def __init__(self, parent, product, **kwargs):
        super().__init__(parent, product_id=product.entity_id, **kwargs)
        self.product = product

    @step("@href")
    def step(self, href, **kwargs):
        """
        Perform step to specific item in Navigation with use of href locator.
        This step function is used by Navigator. Every item in Navigation Menu contains link to the specific View.
        Navigator calls this function with href parameter (Views path), Step then locates correct
        item from Navigation Menu and clicks on it.
        """
        self.nav.select_href(href, **kwargs)

    def prerequisite(self):
        return ProductsView

    @property
    def is_displayed(self):
        return (
            self.nav.is_displayed
            and self.nav.nav_links() == self.NAV_ITEMS
            and self.nav.nav_resource() == self.product["name"]
        )
