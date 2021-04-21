"""Essential Views for Product Views"""
from widgetastic_patternfly4 import PatternflyTable

from testsuite.ui.navigation import step
from testsuite.ui.views.admin.foundation import BaseAdminView
from testsuite.ui.widgets import Link, NavigationMenu


class ProductsView(BaseAdminView):
    """View representation of Product Listing page"""
    endpoint_path = "/apiconfig/services"
    create_product_button = Link("//a[@href='/apiconfig/services/new']")
    table = PatternflyTable("//*[@id='products']/section/table", column_widgets={
        "Name": Link("./a")
    })

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
        return self.endpoint_path in self.browser.url and self.table.is_displayed


class BaseProductView(BaseAdminView):
    """
    Parent View for Product Views. Navigation menu for Product Views contains title with system_name of currently
    displayed Product (this applies for all Views that inherits from BaseProductView).
    This value is verified in `is_displayed` method.
    """
    NAV_ITEMS = ['Overview', 'Analytics', 'Applications', 'ActiveDocs', 'Integration']
    nav = NavigationMenu(id='mainmenu')

    def __init__(self, parent, product, **kwargs):
        super().__init__(parent, product_id=product.entity_id, **kwargs)
        self.product = product

    @step("@href")
    def step(self, href, **kwargs):
        """
        Perform step to specific item in Navigation with use of href locator.
        This step function is used by Navigator. Every item in Navigation Menu contains link to the specific View.
        Navigator calls this function with href parameter (Views endpoint_path), Step then locates correct
        item from Navigation Menu and clicks on it.
        """
        self.nav.select_href(href, **kwargs)

    def prerequisite(self):
        return ProductsView

    @property
    def is_displayed(self):
        if not self.nav.is_displayed:
            return False

        present_nav_items = set(self.nav.nav_links()) & set(self.NAV_ITEMS)
        return BaseAdminView.is_displayed and len(present_nav_items) > 3 \
            and self.nav.nav_resource() == self.product['system_name']
