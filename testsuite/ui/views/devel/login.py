"""Representation of login specific Views"""

from widgetastic.widget import TextInput, Text, View, GenericLocatorWidget

from testsuite.ui.exception import UIException
from testsuite.ui.navigation import step
from testsuite.ui.views.common.foundation import FlashMessage
from testsuite.ui.widgets.buttons import ThreescaleSubmitButton
from testsuite.ui.views.auth import RhssoView, Auth0View
from testsuite.ui.views.devel import BaseDevelView, SignUpView
from testsuite.ui.views.common.login import LoginForm


class ReCaptcha(View):
    """View that represents the reCAPTCHA box"""

    # Frame variable is needed due to implementation of Recaptcha via IFrame and nested view in test(works as ROOT)
    invisible_recaptcha = GenericLocatorWidget("//div[contains(@class,'grecaptcha-logo')]")

    @property
    def is_displayed(self):
        return self.invisible_recaptcha.is_displayed


class LoginView(BaseDevelView):
    """Login View for Devel portal"""

    path_pattern = "/login"
    login_widget = View.nested(LoginForm)
    auth0_link = Text("//*[contains(@class,'auth-provider-auth0')]")
    rhsso_link = Text("//*[contains(@class,'auth-provider-keycloak')]")
    forgot_passwd = Text("//*[contains(text(),'Forgot password?')]")
    flash_message = View.nested(FlashMessage)
    recaptcha = GenericLocatorWidget("//div[contains(@class,'grecaptcha-logo')]")
    skip_wait_displayed = True

    @step("ForgotPasswordView")
    def forgot_password(self):
        """Navigate to forgot password view"""
        self.forgot_passwd.click()

    def do_login(self, name, password):
        """Perform login"""
        self.login_widget.do_login(name, password)

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
        return (
            self.path_pattern in self.browser.url
            and self.login_widget.username_field.is_displayed
            and self.login_widget.password_field.is_displayed
            and self.login_widget.submit.is_displayed
        )


class BasicSignUpView(SignUpView):
    """View for Sign Up into devel portal as developer with default sign up flow"""

    path_pattern = "/signup"
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

    def prerequisite(self):
        return LoginView

    @property
    def is_displayed(self):
        return (
            SignUpView.is_displayed.fget(self)
            and self.organization.is_displayed
            and self.path in self.browser.url
            and self.password.is_displayed
            and self.password2.is_displayed
        )


class InvitationSignupView(SignUpView):
    """View for Invitation Sign Up into devel portal"""

    path_pattern = "/signup"
    username = TextInput(id="user_username")
    email = TextInput(id="user_email")
    password = TextInput(id="user_password")
    password2 = TextInput(id="user_password_confirmation")
    recaptcha = GenericLocatorWidget("//div[contains(@class,'grecaptcha-logo')]")
    skip_wait_displayed = True

    def sign_up(self, username: str, passwd: str, submit: bool = True):
        """
        Signs up an account with provided arguments in developer portal
        """
        if username:
            self.username.fill(username)
        self.password.fill(passwd)
        self.password2.fill(passwd)
        if submit:
            self.signup_button.click()

    @property
    def is_displayed(self):
        return (
            self.username.is_displayed
            and self.path in self.browser.url
            and self.password.is_displayed
            and self.password2.is_displayed
        )


class SuccessfulAccountCreationView(BaseDevelView):
    """View with successful message after account creation in dev portal"""

    path_pattern = "/signup/success"
    thank_you = Text("//div[contains(@class, 'panel-body panel-footer')]/h2")

    @property
    def is_displayed(self):
        return (
            BaseDevelView.is_displayed.fget(self)
            and self.path in self.browser.url
            and self.thank_you.text == "Thank you"
        )


class ForgotPasswordView(BaseDevelView):
    """View for recovering the lost developer account password"""

    path_pattern = "/admin/account/password/new"
    email = TextInput(id="email")
    recaptcha = GenericLocatorWidget("//div[contains(@class,'grecaptcha-logo')]")
    reset_button = ThreescaleSubmitButton()
    flash_message = View.nested(FlashMessage)

    def fill_form(self, email: str):
        """
        fills up the email in the form
        """
        self.email.fill(email)

    def reset_password(self, email: str):
        """Reset password for provided email"""
        self.email.fill(email)
        self.reset_button.click()

    def prerequisite(self):
        return LoginView

    @property
    def is_displayed(self):
        return self.path in self.browser.url and self.email.is_displayed and self.reset_button.is_displayed
