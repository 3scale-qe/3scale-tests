"""View representations of Backend pages"""
from widgetastic.widget import TextInput
from widgetastic.widget import Text

from testsuite.ui.navigation import step
from testsuite.ui.views.admin.backend import BackendsView, BaseBackendView
from testsuite.ui.views.admin.foundation import BaseAdminView
from testsuite.ui.widgets.buttons import ThreescaleUpdateButton, ThreescaleDeleteButton, ThreescaleSubmitButton


class BackendNewView(BaseAdminView):
    """View representation of New Backend page"""

    path_pattern = "p/admin/backend_apis/new"
    name = TextInput(id="backend_api_name")
    system_name = TextInput(id="backend_api_system_name")
    description = TextInput(id="backend_api_description")
    endpoint = TextInput(id="backend_api_private_endpoint")
    create_button = ThreescaleSubmitButton()

    def create(self, name: str, system_name: str, desc: str, endpoint: str):
        """Create new  Backend"""
        self.name.fill(name)
        self.system_name.fill(system_name)
        self.description.fill(desc)
        self.endpoint.fill(endpoint)
        self.create_button.click()

    def prerequisite(self):
        return BackendsView

    @property
    def is_displayed(self):
        return (
            BaseAdminView.is_displayed.fget(self)
            and self.path in self.browser.url
            and self.name.is_displayed
            and self.system_name.is_displayed
        )


class BackendDetailView(BaseBackendView):
    """View representation of Backend detail page"""

    path_pattern = "p/admin/backend_apis/{backend_id}"
    edit_button = Text("//*[contains(@href,'edit')]")

    @step("BackendEditView")
    def edit(self):
        """Edit Backend"""
        self.edit_button.click()

    def prerequisite(self):
        return BaseBackendView

    @property
    def is_displayed(self):
        return (
            BaseBackendView.is_displayed.fget(self) and self.path in self.browser.url and self.edit_button.is_displayed
        )


class BackendEditView(BaseBackendView):
    """View representation of Edit Backend page"""

    path_pattern = "p/admin/backend_apis/{backend_id}/edit"
    name = TextInput(id="backend_api_name")
    system_name = TextInput(id="backend_api_system_name")
    description = TextInput(id="backend_api_description")
    endpoint = TextInput(id="backend_api_private_endpoint")
    update_button = ThreescaleUpdateButton()
    delete_button = ThreescaleDeleteButton()

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

    def prerequisite(self):
        return BackendDetailView

    @property
    def is_displayed(self):
        return (
            BaseBackendView.is_displayed.fget(self)
            and self.path in self.browser.url
            and self.name
            and self.system_name.is_displayed
        )
