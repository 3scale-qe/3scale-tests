"""
View representations of Webhook pages
"""

from widgetastic.widget import TextInput, GenericLocatorWidget, Checkbox


from testsuite.ui.views.admin.settings import BaseSettingsView
from testsuite.ui.widgets import PfCheckBoxGroup
from testsuite.ui.widgets.buttons import ThreescaleUpdateButton


class WebhooksView(BaseSettingsView):
    """
    View representation of Webhook page
    """

    path_pattern = "/p/admin/webhooks/edit"
    webhook_active = GenericLocatorWidget('//*[@id="web_hook_active"]')
    webhook_provider = GenericLocatorWidget('//*[@id="web_hook_provider_actions"]')
    url = TextInput(id="web_hook_url")
    update = ThreescaleUpdateButton()
    accounts_cb_group = PfCheckBoxGroup(label_text="Accounts")
    users_cb_group = PfCheckBoxGroup(label_text="Users")
    applications_cb_group = PfCheckBoxGroup(label_text="Applications")
    keys_cb_group = PfCheckBoxGroup(label_text="Keys")

    def webhook_check(self, webhook_type: str, requestbin: str):
        """Configure given webhooks"""
        self.webhook_active.click()
        self.webhook_provider.click()
        self.url.fill(requestbin)

        if webhook_type == "Accounts":
            self.accounts_cb_group.check_all()

        if webhook_type == "Users":
            self.users_cb_group.check_all()

        if webhook_type == "Applications":
            self.applications_cb_group.check_all()

        if webhook_type == "Keys":
            self.keys_cb_group.check_all()

        self.update.click()

    def prerequisite(self):
        return BaseSettingsView

    @property
    def is_displayed(self):
        return (
            BaseSettingsView.is_displayed.fget(self)
            and self.webhook_active.is_displayed
            and self.webhook_provider.is_displayed
            and self.path in self.browser.url
        )
