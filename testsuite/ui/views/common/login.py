"""Login portion which is the same for admin and master"""
from widgetastic.widget import TextInput, View, Text

from testsuite.ui.widgets.buttons import ThreescaleSubmitButton


class LoginForm(View):
    """
        Basic login functionality in login page
    """
    username_field = TextInput(id='session_username')
    username_label = Text('//input[@id="session_username"]/preceding-sibling::label')
    password_field = TextInput(id='session_password')
    password_label = Text('//input[@id="session_password"]/preceding-sibling::label')
    submit = ThreescaleSubmitButton()

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

    @property
    def is_displayed(self):
        return self.username_field.is_displayed and self.password_field.is_displayed and self.submit.is_displayed and \
               'Email or Username' in self.username_label.text and 'Password' in self.password_label.text
