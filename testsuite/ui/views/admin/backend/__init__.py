"""Essential Views for Backends Views"""
from widgetastic_patternfly4 import PatternflyTable

from testsuite.ui.navigation import step
from testsuite.ui.views.admin.foundation import BaseAdminView
from testsuite.ui.widgets import NavigationMenu, Link


class BackendsView(BaseAdminView):
    """View representation of Backend Listing page"""
    endpoint_path = "p/admin/backend_apis"
    create_backend_button = Link("//a[@href='/p/admin/backend_apis/new']")
    table = PatternflyTable("//*[@id='backend-apis']/section/table", column_widgets={
        "Name": Link("./a")
    })

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
        return BaseAdminView.is_displayed and self.endpoint_path in self.browser.url \
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
        Navigator calls this function with href parameter (Views endpoint_path), Step then locates correct
        item from Navigation Menu and clicks on it.
        """
        self.nav.select_href(href, **kwargs)

    def prerequisite(self):
        return BackendsView

    @property
    def is_displayed(self):
        if not self.nav.is_displayed:
            return False

        present_nav_items = set(self.nav.nav_links()) & set(self.NAV_ITEMS)
        return len(present_nav_items) > 3 and self.nav.nav_resource() == self.backend['system_name']
