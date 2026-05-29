"""
Module contains Base View used for all Master Views. BaseMasterView is further extended.
All of them creates basic page structure for respective Master portal pages.
"""

from widgetastic.widget import GenericLocatorWidget, Text, View
from widgetastic_patternfly4 import Button
from widgetastic_patternfly4.ouia import Dropdown

from testsuite.ui.navigation import Navigable, step


class BaseMasterView(View, Navigable):
    """
    Basic representation of logged in master portal page.
    All master portal pages should inherit from this class.
    """

    path_pattern = ""
    logo = GenericLocatorWidget(".//a[@href='/p/admin/dashboard']")
    support_link = Text("//a[@href='//access.redhat.com/products/red-hat-3scale#support']")
    master_header = Text("//*[contains(@class,'Header--master')]")
    context_menu = Dropdown(component_id="context-selector")
    documentation = Dropdown(component_id="OUIA-Generated-DropdownToggle-2")
    user_session = Dropdown(component_id="OUIA-Generated-DropdownToggle-3")
    threescale_version = Text("//*[contains(@class,'powered-by-3scale')]/span")

    def __init__(self, parent, logger=None, **kwargs):
        super().__init__(parent, logger=logger, **kwargs)
        self.path = self.path_pattern.format_map(kwargs)

    def logout(self):
        """Method which logouts current user from master portal"""
        self.user_session.item_select("Sign Out")

    @step("BaseMasterAudienceView")
    def audience(self):
        """Selects Audience item from ContextSelector"""
        self.context_menu.item_select("Audience")

    @step("MasterDashboardView")
    def dashboard(self):
        """Select Dashboard from ContextSelector"""
        self.context_menu.item_select("Dashboard")

    @property
    def is_displayed(self):
        return (
            self.logo.is_displayed
            and self.documentation.is_displayed
            and self.support_link.is_displayed
            and self.context_menu.is_displayed
            and self.user_session.is_displayed
        )


class MasterDashboardView(BaseMasterView):
    """Dashboard view page object that can be found on path"""

    path_pattern = "/p/admin/dashboard"
    account_link = Text('//a[@href="/buyers/accounts"]')
    application_link = Text('//a[@href="/p/admin/applications"]')
    message_link = Text('//a[@href="/p/admin/messages"]')
    explore_all_products = Text('//a[@href="/apiconfig/services"]')
    explore_all_backends = Text('//a[@href="/p/admin/backend_apis"]')

    @View.nested
    # pylint: disable=invalid-name
    class backends(View):
        """Backends page object"""

        backend_title = Text(locator='//*[@id="backends-widget"]/article/div[1]/div[1]/h1')
        create_backend_button = Button(locator='//a[@href="/p/admin/backend_apis/new"]')

        @property
        def is_displayed(self):
            return self.backend_title.is_displayed and self.create_backend_button.is_displayed

    @View.nested
    # pylint: disable=invalid-name
    class products(View):
        """Products page object"""

        products_title = Text(locator='//*[@id="products-widget"]/article/div[1]/div[1]/h1')

        @property
        def is_displayed(self):
            return self.products_title.is_displayed

    def prerequisite(self):
        return BaseMasterView

    @property
    def is_displayed(self):
        return (
            self.path in self.browser.url
            and self.message_link.is_displayed
            and self.products.is_displayed
            and self.backends.is_displayed
            and self.account_link.is_displayed
            and self.application_link.is_displayed
        )
