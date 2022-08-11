"""Essential Views for Backends Views"""
from widgetastic_patternfly4 import PatternflyTable
from widgetastic.widget import Text, TextInput, GenericLocatorWidget

from testsuite.ui.navigation import step
from testsuite.ui.views.admin.foundation import BaseAdminView
from testsuite.ui.widgets import NavigationMenu


class BackendsView(BaseAdminView):
    """View representation of Backend Listing page"""
    path_pattern = "p/admin/backend_apis"
    create_backend_button = Text("//a[@href='/p/admin/backend_apis/new']")
    table = PatternflyTable("//*[@id='backend-apis']/section/table", column_widgets={
        "Name": Text("./a")
    })
    search_bar = TextInput(locator="//input[@type='search']")
    search_button = GenericLocatorWidget("//button[contains(@aria-label,'search')]")

    def search(self, value: str):
        """Search in backend table by given value"""
        self.search_bar.fill(value)
        self.search_button.click()

    @step("BaseBackendView")
    def detail(self, backend):
        """Detail of Backend"""
        self.table.row(system_name__contains=backend.entity_name).name.widget.click()

    @step("BackendNewView")
    def create_backend(self):
        """Create new Backend"""
        self.create_backend_button.click()

    def prerequisite(self):
        return BaseAdminView

    @property
    def is_displayed(self):
        return BaseAdminView.is_displayed and self.path in self.browser.url \
               and self.create_backend_button.is_displayed and self.table.is_displayed


class BaseBackendView(BaseAdminView):
    """
    Parent View for Backend Views. Navigation menu for Backend Views contains title with system_name of currently
    displayed Backend (this applies for all Views that inherits from BaseBackendView).
    This value is verified in `is_displayed` method.
    """
    NAV_ITEMS = ['Overview', 'Analytics', 'Methods & Metrics', 'Mapping Rules']
    nav = NavigationMenu(id='mainmenu')

    def __init__(self, parent, backend, **kwargs):
        super().__init__(parent, backend_id=backend.entity_id, **kwargs)
        self.backend = backend

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
        return BackendsView

    @property
    def is_displayed(self):
        return self.nav.is_displayed and self.nav.nav_links() == self.NAV_ITEMS \
               and self.nav.nav_resource() == self.backend['name']
