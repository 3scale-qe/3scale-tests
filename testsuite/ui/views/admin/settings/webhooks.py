"""
View representations of Webhook pages
"""
from widgetastic.widget import TextInput, GenericLocatorWidget

from testsuite.ui.views.admin.settings import BaseSettingsView
from testsuite.ui.widgets import CheckBoxGroup
from testsuite.ui.widgets.buttons import ThreescaleUpdateButton


class WebhooksView(BaseSettingsView):
    """
    View representation of Webhook page
    """
    path_pattern = '/p/admin/webhooks/edit'
    webhook_active = GenericLocatorWidget('//*[@id="web_hook_active"]')
    webhook_provider = GenericLocatorWidget('//*[@id="web_hook_provider_actions"]')
    accounts = CheckBoxGroup('//*/fieldset[contains(@name,"trigger webhooks")]',
                             field_set_identifier="Accounts")
    users = CheckBoxGroup('//*/fieldset[contains(@name,"trigger webhooks")]',
                          field_set_identifier="Users")
    applications = CheckBoxGroup('//*/fieldset[contains(@name,"trigger webhooks")]',
                                 field_set_identifier="Applications")
    keys = CheckBoxGroup('//*/fieldset[contains(@name,"trigger webhooks")]',
                         field_set_identifier="Keys")
    checkbox_names = {"Accounts": ["web_hook_account_created_on", "web_hook_account_updated_on",
                                   "web_hook_account_plan_changed_on", "web_hook_account_deleted_on"],
                      "Users": ["web_hook_user_created_on", "web_hook_user_updated_on", "web_hook_user_deleted_on"],
                      "Applications": ["web_hook_application_created_on", "web_hook_application_updated_on",
                                       "web_hook_application_suspended_on", "web_hook_application_plan_changed_on",
                                       "web_hook_application_user_key_updated_on", "web_hook_application_deleted_on"],
                      "Keys": ["web_hook_application_key_created_on", "web_hook_application_key_deleted_on",
                               "web_hook_application_key_updated_on"]}
    url = TextInput(id='web_hook_url')
    update = ThreescaleUpdateButton()

    def webhook_check(self, webhook_type: str, requestbin: str):
        """Configure given webhooks"""
        self.webhook_active.click()
        self.webhook_provider.click()
        self.url.fill(requestbin)

        if webhook_type == "Accounts":
            self.accounts.check(self.checkbox_names[webhook_type])

        if webhook_type == "Users":
            self.users.check(self.checkbox_names[webhook_type])

        if webhook_type == "Applications":
            self.applications.check(self.checkbox_names[webhook_type])

        if webhook_type == "Keys":
            self.keys.check(self.checkbox_names[webhook_type])

        self.update.click()

    def prerequisite(self):
        return BaseSettingsView

    @property
    def is_displayed(self):
        return BaseSettingsView.is_displayed.fget(self) and self.webhook_active.is_displayed \
               and self.webhook_provider.is_displayed and self.path in self.browser.url
