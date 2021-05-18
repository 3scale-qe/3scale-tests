"""Representation of login specific Views"""
from widgetastic.widget import TextInput, GenericLocatorWidget

from testsuite.ui.views.devel import BaseDevelView


class LoginDevelView(BaseDevelView):
    """Login View for Devel portal"""
    path_pattern = '/login'
    username_field = TextInput(id='session_username')
    password_field = TextInput(id='session_password')
    sing_in_btn = GenericLocatorWidget(".//input[@type='submit']")

    def do_login(self, name, password):
        """Perform login"""
        self.username_field.fill(name)
        self.password_field.fill(password)
        self.sing_in_btn.click()

    @property
    def is_displayed(self, ):
        return self.path_pattern in self.browser.url and self.username_field.is_displayed and \
               self.password_field.is_displayed and self.sing_in_btn.is_displayed
