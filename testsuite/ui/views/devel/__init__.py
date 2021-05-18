"""Contains basic views for Developer portal"""
from widgetastic.widget import View, Text, TextInput, GenericLocatorWidget

from testsuite.ui.navigation import Navigable
from testsuite.ui.widgets import Link


class Navbar(View):
    """Represents top navigation menu for logged in Devel Views
    TODO: When browser is not maximized, this menu is collapsed. Add dynamical interaction"""
    ROOT = "//nav[@role='navigation']"

    applications_btn = Link("//a[@href='/admin/applications']")
    statistics_btn = Link("//a[@href='/buyer/stats']")
    documentation_btn = Link("//a[@href='/docs']")
    messages_btn = Link("//a[contains(@href, '/admin/messages/received')]")
    settings_btn = Link("//a[@href='/admin/account']")
    sign_out_btn = Link("//a[contains(@href, '/logout')]")

    @property
    def is_displayed(self):
        return self.applications_btn.is_displayed and \
               self.documentation_btn.is_displayed and self.messages_btn.is_displayed and \
               self.settings_btn.is_displayed and self.sign_out_btn.is_displayed


class BaseDevelView(View, Navigable):
    """
    Parent View for all the logged in Devel Views.
    Features post_navigate step that fill access_code if required.
    """
    path_pattern = ''
    navbar = View.nested(Navbar)

    def __init__(self, parent, access_code=None, logger=None, **kwargs):
        super().__init__(parent, logger=logger, **kwargs)
        self.access_code = access_code
        self.path = self.path_pattern.format_map(kwargs)

    # pylint: disable=using-constant-test
    def post_navigate(self, **kwargs):
        access_view = AccessView(self.browser.root_browser)
        if access_view.is_displayed:
            access_view.access_code(self.access_code)


class LandingView(BaseDevelView):
    """Developer portal landing page"""
    sign_in_btn = Link("//a[contains(@href, '/login')]")

    @property
    def is_displayed(self):
        return self.sign_in_btn.is_displayed


class AccessView(View):
    """View for Access Code"""
    access_code_label = Text('//label')
    access_code_field = TextInput(id='access_code')
    enter_btn = GenericLocatorWidget("//input[@type='submit']")

    def access_code(self, code):
        """Fill access_code"""
        self.access_code_field.fill(code)
        self.enter_btn.click()

    @property
    def is_displayed(self):
        return self.access_code_label.is_displayed and \
               self.access_code_label.text == 'Access code' and \
               self.access_code_field.is_displayed
