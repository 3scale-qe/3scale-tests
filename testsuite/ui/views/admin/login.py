""" Representation of Login specific views"""

from widgetastic.widget import View, Text, TextInput, GenericLocatorWidget
from widgetastic_patternfly4.ouia import Button

from testsuite.ui.exception import UIException
from testsuite.ui.navigation import Navigable, step
from testsuite.ui.views.admin.wizard import WizardIntroView
from testsuite.ui.views.auth import Auth0View, RhssoView
from testsuite.ui.views.common.login import LoginForm


class LoginView(View, Navigable):
    """
    Basic login view page object that can be found on path
    """

    path = "/p/login"
    ROOT = "/html//div[@id='pf-login-page-container']"
    header = Text("//main/header/h2")
    error_message = Text("//h4[@class='pf-c-alert__title']")
    login_widget = View.nested(LoginForm)
    password_reset_link = Text("//a[@href='/p/password/reset']")
    auth0_link = Text("//*[@class='login-provider-link' and contains(@href,'auth0')]")
    rhsso_link = Text("//*[@class='login-provider-link' and contains(@href,'keycloak')]")

    @step("RequestAdminPasswordView")
    def reset_password(self):
        """Process to next page"""
        self.password_reset_link.click()

    def do_login(self, name, password):
        """
        Method handle login to 3scale admin portal
        :param name: User username for login
        :param password: User password for login
        :return DashboardView page object
        """
        self.login_widget.do_login(name, password)
        if "/p/admin/onboarding/wizard/intro" in self.browser.url:
            wizard = WizardIntroView(self.browser.root_browser)
            wizard.close_wizard()

    def do_auth0_login(self, email, password):
        """
        Method handle login to 3scale admin portal via Auth0
        :param email: User email for login
        :param password: User password for login
        :return DashboardView page object
        """
        if not self.auth0_link.is_displayed:
            raise UIException("Auth0 provider is not configured for admin portal")
        self.auth0_link.click()
        auth = Auth0View(self.browser.root_browser)
        auth.login(email, password)

    def do_rhsso_login(self, username, password, realm=None):
        """
        Method handle login to 3scale admin portal via RHSSO
        :param username: User email for login
        :param password: User password for login
        :param realm: RHSSO realm name (if more than one RHSSO integration is used)
        :return DashboardView page object
        """
        if not self.rhsso_link.is_displayed:
            raise UIException("RHSSO provider is not configured for admin portal")
        if realm:
            # RHOAM creates its own RHSSO integration, which we don't want to use
            self.browser.element(f"//a[contains(@href,'{realm}')]").click()
        else:
            self.rhsso_link.click()
        auth = RhssoView(self.browser.root_browser)
        auth.login(username, password)

    @property
    def is_displayed(self):
        return (
            self.password_reset_link.is_displayed
            and self.path in self.browser.url
            and self.browser.title == "3scale Login"
            and "Log in to your account" in self.header.text
            and self.login_widget.is_displayed
        )


class RequestAdminPasswordView(View, Navigable):
    """
    View page object to request password reset
    """

    path = "/p/password/reset"
    password_reset_field = TextInput(id="email")
    passwd_reset_btn = Button(component_id="OUIA-Generated-Button-primary-1")

    def reset_password(self, email):
        """Reset password of email address user"""
        self.password_reset_field.fill(email)
        self.passwd_reset_btn.click()

    def prerequisite(self):
        """Page prerequisite used by navigator"""
        return LoginView

    @property
    def is_displayed(self):
        return (
            self.password_reset_field.is_displayed
            and self.path in self.browser.url
            and self.passwd_reset_btn.is_displayed
        )


class ResetPasswordView(View, Navigable):
    """
    Reset password view page object
    """

    password = TextInput(id="user_password")
    passwd_confirmation = TextInput(id="user_password_confirmation")
    change_password_btn = GenericLocatorWidget("//*[@type='submit' or @value='Change Password']")

    def change_password(self, new_password):
        """Reset password of email address user"""
        self.password.fill(new_password)
        self.passwd_confirmation.fill(new_password)
        self.change_password_btn.click()

    @property
    def is_displayed(self):
        return self.password.is_displayed and self.passwd_confirmation.is_displayed
