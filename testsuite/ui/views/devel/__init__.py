"""Contains basic views for Developer portal"""
from widgetastic.widget import View, Text, TextInput, GenericLocatorWidget

from testsuite.ui.navigation import Navigable, step
from testsuite.ui.widgets import ActiveDocV3Section


class Navbar(View, Navigable):
    """Represents top navigation menu for logged in Devel Views"""

    ROOT = "//nav[@role='navigation']"

    applications_btn = Text("//a[@href='/admin/applications']")
    statistics_btn = Text("//a[@href='/buyer/stats']")
    documentation_btn = Text("//a[@href='/docs']")
    messages_btn = Text("//a[contains(@href, '/admin/messages/received')]")
    settings_btn = Text("//a[@href='/admin/account']")
    sign_out_btn = Text("//a[contains(@href, '/logout')]")

    @step("SettingsTabs")
    def settings(self):
        """Settings"""
        self.settings_btn.click()

    @step("InboxView")
    def messages(self):
        """Messages"""
        self.messages_btn.click()

    @property
    def is_displayed(self):
        return (
            self.applications_btn.is_displayed
            and self.documentation_btn.is_displayed
            and self.messages_btn.is_displayed
            and self.settings_btn.is_displayed
            and self.sign_out_btn.is_displayed
        )


class BaseDevelView(View, Navigable):
    """
    Parent View for all the logged in Devel Views.
    Features post_navigate step that fill access_code if required.
    """

    path_pattern = ""
    navbar = View.nested(Navbar)
    footer_logo = GenericLocatorWidget(locator='//*[@class="powered-by"]')
    navbar_brand = GenericLocatorWidget(locator='//*[@class="navbar-brand"]')

    def __init__(self, parent, access_code=None, logger=None, **kwargs):
        super().__init__(parent, logger=logger, **kwargs)
        self.access_code = access_code
        self.path = self.path_pattern.format_map(kwargs)

    @property
    def is_logged_in(self):
        """Detect if user is logged in developer portal"""
        return self.navbar.sign_out_btn.is_displayed

    # pylint: disable=using-constant-test
    def post_navigate(self, **kwargs):
        access_view = AccessView(self.browser.root_browser)
        if access_view.is_displayed:
            access_view.access_code(self.access_code)

    @step("DocsView")
    def settings(self):
        """Documentation"""
        self.navbar.documentation_btn.click()

    @property
    def is_displayed(self):
        return self.footer_logo.is_displayed and self.navbar_brand.is_displayed


class LandingView(BaseDevelView):
    """Developer portal landing page"""

    sign_in_btn = Text("//a[contains(@href, '/login')]")
    close_csm = GenericLocatorWidget('//*[@id="cms-toolbar-menu-right"]/li/a')

    @property
    def is_displayed(self):
        return self.sign_in_btn.is_displayed

    def post_navigate(self, **kwargs):
        super().post_navigate(**kwargs)
        if self.close_csm.is_displayed:
            self.close_csm.click()


class AccessView(View):
    """View for Access Code"""

    access_code_label = Text("//label")
    access_code_field = TextInput(id="access_code")
    enter_btn = GenericLocatorWidget("//input[@type='submit']")

    def access_code(self, code):
        """Fill access_code"""
        self.access_code_field.fill(code)
        self.enter_btn.click()

    @property
    def is_displayed(self):
        return (
            self.access_code_label.is_displayed
            and self.access_code_label.text == "Access code"
            and self.access_code_field.is_displayed
        )


class SignUpView(BaseDevelView):
    """View for Sign Up into devel portal"""

    path_pattern = "/signup"
    organization = TextInput(id="account_org_name")
    username = TextInput(id="account_user_username")
    email = TextInput(id="account_user_email")
    signup_button = GenericLocatorWidget("//input[@type='submit']")

    def signup(self, org: str, username: str = None, email: str = None, submit: bool = True):
        """Signup into devel portal"""
        self.organization.wait_displayed()
        self.organization.fill(org)
        if username:
            self.username.fill(username)
        if email:
            self.email.fill(email)
        if submit:
            self.signup_button.click()

    @property
    def is_displayed(self):
        return (
            BaseDevelView.is_displayed.fget(self)
            and self.path in self.browser.url
            and self.organization.is_displayed
            and self.username.is_displayed
            and self.email.is_displayed
        )


class DocsView(BaseDevelView):
    """View for Documentation page of devel portal"""

    path_pattern = "/docs"
    active_docs_section = ActiveDocV3Section()

    def __init__(self, parent, path=None):
        super().__init__(parent)
        if path:
            self.path = path

    # pylint: disable=no-self-use
    def prerequisite(self):
        return BaseDevelView

    @property
    def is_displayed(self):
        return (
            BaseDevelView.is_displayed.fget(self)
            and self.path in self.browser.url
            and self.active_docs_section.is_displayed
        )
