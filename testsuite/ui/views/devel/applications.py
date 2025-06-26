"""Devel applications pages and tabs"""

from widgetastic.widget import Table, Text

from testsuite.ui.navigation import step
from testsuite.ui.views.devel import BaseDevelView, Navbar
from testsuite.ui.widgets.buttons import ThreescaleButton


class ApplicationsListView(BaseDevelView):
    """Applications list view in dev portal"""

    path_pattern = "/admin/applications"
    create_app_btn = Text("//a[contains(@href,'admin/messages/trash')]")
    app_table = Table('.//table[@id="applications"]')

    @step("DevelApplicationDetailView")
    def details(self, application):
        """Application detail view"""
        self.app_table.row(name=application.entity_name).name.click()

    def prerequisite(self):
        return Navbar

    @property
    def is_displayed(self):
        return self.path in self.browser.url


class DevelApplicationDetailView(BaseDevelView):
    """Dev application detail view"""

    path_pattern = "/admin/applications/{application_id}"
    change_plan_link = Text("//a[contains(@id,'choose-plan-')]")

    def __init__(self, parent, application):
        super().__init__(parent, application_id=application.entity_id)

    def change_plan(self, plan_id):
        """Make request for plan change from dev portal"""
        self.change_plan_link.click()
        plan_link = Text(self, f"//a[@data-plan-id='{plan_id}']")
        plan_link.click()
        request_btn = ThreescaleButton(
            self, "Request Plan Change", classes=["plan-change-button"], id=f"change-plan-{plan_id}"
        )
        request_btn.click()

    def prerequisite(self):
        return ApplicationsListView

    @property
    def is_displayed(self):
        return self.change_plan_link.is_displayed and self.path in self.browser.url
