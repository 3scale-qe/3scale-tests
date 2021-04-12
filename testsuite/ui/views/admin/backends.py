"""View representations of Backend pages"""
from widgetastic.widget import TextInput
from widgetastic_patternfly4 import PatternflyTable

from testsuite.ui.navigation import step
from testsuite.ui.views.admin import BaseAdminView
from testsuite.ui.views.admin.foundation import BackendNavView
from testsuite.ui.widgets import Link
from testsuite.ui.widgets.buttons import ThreescaleUpdateButton, ThreescaleDeleteButton, \
    ThreescaleCreateButton


class BackendsView(BaseAdminView):
    """View representation of Backend Listing page"""
    endpoint_path = "p/admin/backend_apis"
    create_backend_button = Link("//a[@href='/p/admin/backend_apis/new']")
    table = PatternflyTable("//*[@id='backend-apis']/section/table", column_widgets={
        "Name": Link("./a")
    })

    # pylint: disable=invalid-overridden-method
    def prerequisite(self):
        return BaseAdminView

    # pylint: disable=invalid-overridden-method
    @property
    def is_displayed(self):
        return BaseAdminView.is_displayed and self.endpoint_path in self.browser.url \
               and self.create_backend_button.is_displayed and self.table.is_displayed

    @step("BackendDetailView")
    def detail(self, backend):
        """Detail of Backend"""
        self.table.row(system_name__contains=backend.entity_name).name.widget.click()

    @step("BackendNewView")
    def create_backend(self):
        """Create new Backend"""
        self.create_backend_button.click()


class BackendNewView(BaseAdminView):
    """View representation of New Backend page"""
    endpoint_path = "p/admin/backend_apis/new"
    name = TextInput(id="backend_api_name")
    system_name = TextInput(id="backend_api_system_name")
    description = TextInput(id="backend_api_description")
    endpoint = TextInput(id="backend_api_private_endpoint")
    create_button = ThreescaleCreateButton()

    # pylint: disable=invalid-overridden-method
    def prerequisite(self):
        return BackendsView

    # pylint: disable=invalid-overridden-method
    @property
    def is_displayed(self):
        return BaseAdminView.is_displayed and self.endpoint_path in self.browser.url \
               and self.name.is_displayed and self.system_name.is_displayed

    def create(self, name: str, system_name: str, desc: str, endpoint: str):
        """Create new  Backend"""
        self.name.fill(name)
        self.system_name.fill(system_name)
        self.description.fill(desc)
        self.endpoint.fill(endpoint)
        self.create_button.click()


class BackendDetailView(BackendNavView):
    """View representation of Backend detail page"""
    endpoint_path = "p/admin/backend_apis/{backend_id}"
    edit_button = Link("//*[contains(@href,'edit')]")

    def prerequisite(self):
        return BackendsView

    @property
    def is_displayed(self):
        return BackendNavView.is_displayed and self.endpoint_path in self.browser.url and self.edit_button.is_displayed

    @step("BackendEditView")
    def edit(self):
        """Edit Backend"""
        self.edit_button.click()


class BackendEditView(BackendNavView):
    """View representation of Edit Backend page"""
    endpoint_path = "p/admin/backend_apis/{backend_id}/edit"
    name = TextInput(id="backend_api_name")
    system_name = TextInput(id="backend_api_system_name")
    description = TextInput(id="backend_api_description")
    endpoint = TextInput(id="backend_api_private_endpoint")
    update_button = ThreescaleUpdateButton()
    delete_button = ThreescaleDeleteButton()

    def prerequisite(self):
        return BackendDetailView

    @property
    def is_displayed(self):
        return BackendNavView.is_displayed and self.endpoint_path in self.browser.url \
               and self.name and self.system_name.is_displayed

    def update(self, name: str = "", desc: str = "", endpoint: str = ""):
        """Update Backend"""
        if name:
            self.name.fill(name)
        if desc:
            self.description.fill(desc)
        if endpoint:
            self.endpoint.fill(endpoint)

        self.update_button.click()

    def delete(self):
        """Delete Backend"""
        self.delete_button.click()
