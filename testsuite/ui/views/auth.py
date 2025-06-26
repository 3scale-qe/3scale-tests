"""View representations of 3rd party auth pages"""

from weakget import weakget
from widgetastic.widget import GenericLocatorWidget, Text, TextInput, View

from testsuite import settings
from testsuite.ui.navigation import Navigable
from testsuite.ui.views.admin.foundation import BaseAdminView


class Auth0View(View, Navigable):
    """View representation of 3rd party Auth0 provider page"""

    url_domain = weakget(settings)["auth0"]["domain"] % None
    email = TextInput(name="email")
    password = TextInput(name="password")
    login_button = GenericLocatorWidget(locator="//button[@aria-label='Log In']")
    last_login_button = GenericLocatorWidget(locator="//*[contains(@class,'auth0-lock-social-button')]")
    last_login_button_text = Text(locator="//*[contains(@class,'auth0-lock-social-button-text')]")
    not_my_account = GenericLocatorWidget(locator="//*[@class='auth0-lock-alternative-link']")

    def login(self, email, password):
        """Login to 3scale via Auth0"""
        self.last_login_button.wait_displayed()
        if not self.email.is_displayed:
            if self.last_login_button_text.text == email:
                self.last_login_button.click()
                return
            self.not_my_account.click()
        self.email.wait_displayed()
        self.email.fill(email)
        self.password.fill(password)
        self.login_button.click()

    @property
    def is_displayed(self):
        return (
            self.email.is_displayed
            and self.password.is_displayed
            and self.login_button.is_displayed
            and self.url_domain in self.browser.url
        )


class RhssoView(View, Navigable):
    """View representation of 3rd party RHSSO provider page"""

    username = TextInput(name="username")
    password = TextInput(name="password")
    login_button = GenericLocatorWidget(locator="//*[@name='login']")

    def login(self, username, password):
        """Login to 3scale via Auth0"""
        is_logged_in = BaseAdminView(self.browser.root_browser).is_displayed
        if not is_logged_in:
            self.username.wait_displayed()
            self.username.fill(username)
            self.password.fill(password)
            self.login_button.click()

    @property
    def is_displayed(self):
        return self.username.is_displayed and self.password.is_displayed and self.login_button.is_displayed
