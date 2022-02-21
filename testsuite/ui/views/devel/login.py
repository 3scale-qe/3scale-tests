"""Representation of login specific Views"""
from widgetastic.widget import TextInput, Text

from testsuite.ui.widgets.buttons import ThreescaleSubmitButton
from testsuite.ui.views.auth import RhssoView, Auth0View
from testsuite.ui.views.devel import BaseDevelView


class LoginDevelView(BaseDevelView):
    """Login View for Devel portal"""
    path_pattern = '/login'
    username_field = TextInput(id='session_username')
    password_field = TextInput(id='session_password')
    sign_in_btn = ThreescaleSubmitButton()
    auth0_link = Text("//*[contains(@class,'auth-provider-auth0')]")
    rhsso_link = Text("//*[contains(@class,'auth-provider-keycloak')]")

    def do_login(self, name, password):
        """Perform login"""
        self.username_field.fill(name)
        self.password_field.fill(password)
        self.sign_in_btn.click()

    def do_auth0_login(self, email, password):
        """
        Method handle login to 3scale devel portal via Auth0
        :param email: User email for login
        :param password: User password for login
        :return DashboardView page object
        """
        if not self.auth0_link.is_displayed:
            raise Exception("Auth0 provider is not configured for admin portal")
        self.auth0_link.click()
        auth = Auth0View(self.browser.root_browser)
        auth.login(email, password)

    def do_rhsso_login(self, username, password):
        """
        Method handle login to 3scale devel portal via RHSSO
        :param email: User email for login
        :param password: User password for login
        :return DashboardView page object
        """
        if not self.rhsso_link.is_displayed:
            raise Exception("RHSSO provider is not configured for admin portal")
        self.rhsso_link.click()
        auth = RhssoView(self.browser.root_browser)
        auth.login(username, password)

    @property
    def is_displayed(self, ):
        return self.path_pattern in self.browser.url and self.username_field.is_displayed and \
               self.password_field.is_displayed and self.sign_in_btn.is_displayed
