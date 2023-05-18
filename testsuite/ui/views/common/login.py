"""Login portion which is the same for admin and master"""
from widgetastic.widget import TextInput, View, Text

from testsuite.ui.widgets.buttons import ThreescaleSubmitButton


class LoginForm(View):
    """
    Basic login functionality in login page
    """

    username_field = TextInput(id="session_username")
    username_label = Text('.//label[@for="session_username"]')
    password_field = TextInput(id="session_password")
    password_label = Text('.//label[@for="session_password"]')
    submit = ThreescaleSubmitButton()

    def fill_passwd(self, passwd: str):
        """Method fill password field with password logging disabled"""
        self.password_field.fill(passwd, sensitive=True)

    def do_login(self, name: str, password: str):
        """
        Method handle login to 3scale admin portal
        :param name: User username for login
        :param password: User password for login
        :return DashboardView page object
        """
        self.username_field.fill(name)
        self.fill_passwd(password)
        self.submit.click()

    @property
    def is_displayed(self):
        return (
            self.username_field.is_displayed
            and self.password_field.is_displayed
            and self.submit.is_displayed
            and "Email or Username" in self.username_label.text
            and "Password" in self.password_label.text
        )
