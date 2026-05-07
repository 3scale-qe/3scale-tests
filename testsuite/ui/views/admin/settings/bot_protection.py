"""View representation of Admin Portal Bot Protection settings page"""

from widgetastic.widget import Text

from testsuite.ui.views.admin.settings import BaseSettingsView
from testsuite.ui.widgets.buttons import ThreescaleSubmitButton


class AdminBotProtection(BaseSettingsView):
    """View representation of Admin Portal Bot Protection settings"""

    path_pattern = "/p/admin/bot_protection/edit"
    no_protection = Text('//*[@id="settings_admin_bot_protection_level_none"]')
    recaptcha_protection = Text('//*[@id="settings_admin_bot_protection_level_captcha"]')
    submit_button = ThreescaleSubmitButton()

    def prerequisite(self):
        return BaseSettingsView

    def disable_protection(self):
        """Disables admin portal bot protection by selecting None and submitting."""
        self.no_protection.click()
        self.submit_button.click()

    def enable_protection(self):
        """Enables admin portal bot protection by selecting reCAPTCHA v3 and submitting."""
        self.recaptcha_protection.click()
        self.submit_button.click()

    @property
    def is_displayed(self):
        return (
            BaseSettingsView.is_displayed.fget(self)
            and self.path in self.browser.url
            and self.no_protection.is_displayed
            and self.recaptcha_protection.is_displayed
        )
