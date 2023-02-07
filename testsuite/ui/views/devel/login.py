"""Representation of login specific Views"""
from time import sleep
from widgetastic.widget import TextInput, Text, View

from testsuite.ui.exception import UIException
from testsuite.ui.views.common.foundation import FlashMessage
from testsuite.ui.widgets.buttons import ThreescaleSubmitButton
from testsuite.ui.views.auth import RhssoView, Auth0View
from testsuite.ui.views.devel import BaseDevelView, SignUpView


class LoginView(BaseDevelView):
    """Login View for Devel portal"""
    path_pattern = '/login'
    username_field = TextInput(id='session_username')
    password_field = TextInput(id='session_password')
    sign_in_btn = ThreescaleSubmitButton()
    auth0_link = Text("//*[contains(@class,'auth-provider-auth0')]")
    rhsso_link = Text("//*[contains(@class,'auth-provider-keycloak')]")
    flash_message = View.nested(FlashMessage)
    skip_wait_displayed = True

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
            raise UIException("Auth0 provider is not configured for admin portal")
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
            raise UIException("RHSSO provider is not configured for admin portal")
        self.rhsso_link.click()
        auth = RhssoView(self.browser.root_browser)
        auth.login(username, password)

    @property
    def is_displayed(self):
        return self.path_pattern in self.browser.url and self.username_field.is_displayed and \
               self.password_field.is_displayed and self.sign_in_btn.is_displayed


class ReCaptcha(View):
    """View that represents the reCAPTCHA box"""
    # Frame variable is needed due to implementation of Recaptcha via IFrame and nested view in test(works as ROOT)
    FRAME = "//iframe[@title='reCAPTCHA']"
    check_box = Text("//div[contains(@class, 'recaptcha-checkbox-borderAnimation')]")

    def check_recaptcha(self):
        """
        Clicks in recaptcha box to successfully pass the recaptcha
        """
        self.check_box.click()
        # Recaptcha check confirmation needs waits at least 0.5 sec to finish recaptcha confirmation flow to enable
        # the verify button
        sleep(1)

    @property
    def is_displayed(self):
        return self.check_box.is_displayed


class BasicSignUpView(SignUpView):
    """View for Sign Up into devel portal as developer with default sign up flow"""
    path_pattern = '/signup'
    password = TextInput(id="account_user_password")
    password2 = TextInput(id="account_user_password_confirmation")
    recaptcha = View.nested(ReCaptcha)

    # pylint: disable=too-many-arguments
    def sign_up(self, org: str, username: str, email: str, password: str, submit: bool = True):
        """
        Signs up an account with provided arguments in developer portal
        """
        self.signup(org, username, email, False)
        self.password.fill(password)
        self.password2.fill(password)
        if submit:
            self.signup_button.click()

    def check_recaptcha(self):
        """
        Checks if reCaptcha exists and if it does, it execute the recaptcha verification
        """
        self.recaptcha.check_recaptcha()

    def prerequisite(self):
        return LoginView

    @property
    def is_displayed(self):
        return SignUpView.is_displayed.fget(self) and self.path in self.browser.url and \
               self.password.is_displayed and self.password2.is_displayed


class SuccessfulAccountCreationView(BaseDevelView):
    """View with successful message after account creation in dev portal"""
    path_pattern = "/signup/success"
    thank_you = Text("//div[contains(@class, 'panel-body panel-footer')]/h2")

    @property
    def is_displayed(self):
        return BaseDevelView.is_displayed.fget(self) and self.path in self.browser.url \
               and self.thank_you.text == "Thank you"


class ForgotPasswordView(BaseDevelView):
    """View for recovering the lost developer account password"""
    path_pattern = "/admin/account/password/new"
    email = TextInput(id="email")
    recaptcha = View.nested(ReCaptcha)
    reset_button = ThreescaleSubmitButton()
    flash_message = View.nested(FlashMessage)

    def fill_form(self, email: str):
        """
        fills up the email in the form
        """
        self.email.fill(email)

    def check_recaptcha(self):
        """
        Checks if reCaptcha exists and if it does, it execute the recaptcha verification
        """
        if not self.recaptcha.is_displayed:
            raise UIException("Recaptcha was not found on the website")
        self.recaptcha.check_recaptcha()

    def prerequisite(self):
        return BaseDevelView

    @property
    def is_displayed(self):
        return BaseDevelView.is_displayed.fget(self) and self.path in self.browser.url and \
               self.email.is_displayed and self.reset_button.is_displayed
