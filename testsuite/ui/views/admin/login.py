""" Representation of Login specific views"""
from widgetastic.widget import TextInput, View, Text
from widgetastic_patternfly4 import Button
from testsuite.ui.views.admin.foundation import DashboardView
from testsuite.ui.views.admin.wizard import WizardIntroView
from testsuite.ui.exception import DestinationNotDisplayedError
from testsuite.ui.widgets import Link


class LoginView(View):
    """
    Basic login view page object that can be found on endpoint_path
    """
    endpoint_path = '/p/login'
    ROOT = "/html//div[@id='pf-login-page-container']"

    header = Text("//main/header/h2")
    error_message = Text("//p[@class='pf-c-form__helper-text pf-m-error']")
    username_field = TextInput(id='session_username')
    username_label = Text('//input[@id="session_username"]/preceding-sibling::label')
    password_field = TextInput(id='session_password')
    password_label = Text('//input[@id="session_password"]/preceding-sibling::label')
    submit = Button(locator=".//button[@type='submit']")
    password_reset_link = Link("//a[@href='/p/password/reset']")

    # pylint: disable=no-else-return
    def do_login(self, name, password):
        """
        Method handle login to 3scale admin portal
        :param name: User username for login
        :param password: User password for login
        :return DashboardView page object
        """
        self.username_field.fill(name)
        self.password_field.fill(password)
        self.submit.click()
        if '/p/admin/dashboard' in self.browser.url:
            return DashboardView(self.browser.root_browser)
        elif '/p/admin/onboarding/wizard/intro' in self.browser.url:
            wizard = WizardIntroView(self.browser.root_browser)
            wizard.close_wizard()
            return DashboardView(self.browser.root_browser)
        else:
            raise DestinationNotDisplayedError

    @property
    def is_displayed(self):
        return self.username_field.is_displayed and self.password_field.is_displayed and \
               self.password_reset_link.is_displayed and self.endpoint_path in self.browser.url and \
               self.browser.title == '3scale Login' and 'Log in to your account' in self.header.text and \
               'Email or Username' in self.username_label.text and 'Password' in self.password_label.text
