"""
View representations of Webhook pages
"""
from widgetastic.widget import TextInput, GenericLocatorWidget

from testsuite.ui.views.admin.foundation import SettingsNavView
from testsuite.ui.widgets import CheckBoxGroup


# pylint: disable=invalid-overridden-method
class WebhooksView(SettingsNavView):
    """
    View representation of Webhook page
    """
    path_pattern = '/p/admin/webhooks/edit'

    webhook_active = GenericLocatorWidget('//*[@id="web_hook_active"]')
    webhook_provider = GenericLocatorWidget('//*[@id="web_hook_provider_actions"]')
    accounts = CheckBoxGroup('//*[@name="Accounts"]')
    users = CheckBoxGroup('//*[@name="Users"]')
    applications = CheckBoxGroup('//*[@name="Applications"]')
    keys = CheckBoxGroup('//*[@name="Keys"]')
    checkbox_names = {"Accounts": ["web_hook_account_created_on", "web_hook_account_updated_on",
                                   "web_hook_account_plan_changed_on", "web_hook_account_deleted_on"],
                      "Users": ["web_hook_user_created_on", "web_hook_user_updated_on", "web_hook_user_deleted_on"],
                      "Applications": ["web_hook_application_created_on", "web_hook_application_updated_on",
                                       "web_hook_application_suspended_on", "web_hook_application_plan_changed_on",
                                       "web_hook_application_user_key_updated_on", "web_hook_application_deleted_on"],
                      "Keys": ["web_hook_application_key_created_on", "web_hook_application_key_deleted_on",
                               "web_hook_application_key_updated_on"]}
    url = TextInput(id='web_hook_url')
    update = GenericLocatorWidget(locator="//input[contains(@type, 'submit')]")

    def prerequisite(self):
        return SettingsNavView

    @property
    def is_displayed(self):
        return self.webhook_active.is_displayed and self.webhook_provider.is_displayed and \
               self.endpoint_path in self.browser.url

    def webhook_check(self, webhook_type: str, requestbin: str):
        """Configure given webhooks"""
        self.webhook_active.click()
        self.webhook_provider.click()
        self.url.fill(requestbin)

        if webhook_type == "Accounts":
            self.accounts.select(self.checkbox_names[webhook_type])

        if webhook_type == "Users":
            self.users.select(self.checkbox_names[webhook_type])

        if webhook_type == "Applications":
            self.applications.select(self.checkbox_names[webhook_type])

        if webhook_type == "Keys":
            self.keys.select(self.checkbox_names[webhook_type])

        self.update.click()
