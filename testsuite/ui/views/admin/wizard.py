""" Introduction wizard pages module"""
from widgetastic.widget import View, GenericLocatorWidget, TextInput
from widgetastic_patternfly import Text
from widgetastic_patternfly4 import Button

from testsuite.ui.navigation import step, Navigable
from testsuite.ui.widgets import Link
from testsuite.ui.widgets.buttons import ThreescaleSubmitButton


class WizardCommonView(View, Navigable):
    """
    All wizard pages common objects
    """
    close_wizard_link = Link("//a[@href='/p/admin/dashboard']")
    logo = GenericLocatorWidget(locator="//*[@id='logo']/span")

    # pylint: disable=pointless-statement
    def close_wizard(self):
        """
        Method which close wizard
        """
        self.close_wizard_link.click()

    @property
    def is_displayed(self):
        return self.close_wizard_link.is_displayed and self.logo.is_displayed


class WizardIntroView(WizardCommonView, Navigable):
    """
    Representation of Wizard introduction view page object.
    """
    endpoint_path = '/p/admin/onboarding/wizard/intro'

    next_button = Button(locator="//a[@href='/p/admin/onboarding/wizard/explain']")
    page_title = Text("//main/h1")

    @step("WizardExplainView")
    def next_page(self):
        """Process to next page"""
        self.next_button.click()

    @property
    def is_displayed(self):
        return self.endpoint_path in self.browser.url and self.next_button.is_displayed \
               and WizardCommonView.is_displayed


class WizardExplainView(WizardCommonView, Navigable):
    """
    Representation of Wizard explain view page object.
    """
    endpoint_path = '/p/admin/onboarding/wizard/explain'

    tenant_url = Text('.code-example__base')
    next_button = Button(locator="//a[@href='/p/admin/onboarding/wizard/backend_api/new']")

    @step("WizardBackendApiView")
    def next_page(self):
        """Process to next page"""
        self.next_button.click()

    # pylint: disable=no-self-use
    def prerequisite(self):
        """Page prerequisite used by navigator"""
        return WizardIntroView

    @property
    def is_displayed(self):
        return self.endpoint_path in self.browser.url and WizardCommonView.is_displayed


class WizardBackendApiView(WizardCommonView, Navigable):
    """
    Representation of Wizard Add Backend API view page object.
    """
    endpoint_path = '/p/admin/onboarding/wizard/backend_api/new'
    backend_name_field = TextInput(id='backend_api_name')
    base_url_field = TextInput(id='backend_api_private_endpoint')
    add_backend_btn = ThreescaleSubmitButton()
    use_echo_api_link = Link("//a[@href='#']")

    @step('WizardProductView')
    def add_backend(self, backend_name: str, base_url: str):
        """Fill backend values and click to navigate to next page"""
        self.backend_name_field.fill(backend_name)
        self.base_url_field.fill(base_url)
        self.add_backend_btn.click()

    def set_echo_api(self):
        """Set base_url to predefined value"""
        self.use_echo_api_link.click()

    # pylint: disable=no-self-use
    def prerequisite(self):
        """Page prerequisite used by navigator"""
        return WizardExplainView

    @property
    def is_displayed(self):
        return self.backend_name_field.is_displayed and WizardCommonView.is_displayed and \
               self.endpoint_path in self.browser.url and self.base_url_field.is_displayed


class WizardEditApiView(WizardCommonView, Navigable):
    """
    Representation of Wizard Edit Backend API view page object.
    """
    endpoint_path = '/p/admin/onboarding/wizard/api/edit'
    base_url_field = TextInput(id='api_backend')
    product_name_field = TextInput(id='api_name')
    page_title = Text("//main/h1")
    update_api_btn = ThreescaleSubmitButton()

    @property
    def is_displayed(self):
        return self.endpoint_path in self.browser.url and WizardCommonView.is_displayed and\
               self.product_name_field.is_displayed and self.base_url_field.is_displayed


class WizardProductView(WizardCommonView, Navigable):
    """
    Representation of Wizard New Product view page object.
    """
    endpoint_path = '/p/admin/onboarding/wizard/product/new'
    product_name_field = TextInput(id='service_name')
    add_product_btn = ThreescaleSubmitButton()

    @step('WizardConnectView')
    def add_product(self, product_name: str):
        """Fill product values and click to navigate to next page"""
        self.product_name_field.fill(product_name)
        self.add_product_btn.click()

    # pylint: disable=no-self-use
    def prerequisite(self):
        """Page prerequisite used by navigator"""
        return WizardBackendApiView

    @property
    def is_displayed(self):
        return self.product_name_field.is_displayed and WizardCommonView.is_displayed and \
               self.endpoint_path in self.browser.url and self.add_product_btn.is_displayed


class WizardConnectView(WizardCommonView, Navigable):
    """
    Representation of Wizard Connect view page object.
    """
    endpoint_path = '/p/admin/onboarding/wizard/connect/new'
    path_field = TextInput(id='backend_api_config_path')
    connect_btn = ThreescaleSubmitButton()

    @step('WizardRequestView')
    def connect_backend_to_product(self, path: str):
        """Fill path value and click to navigate to next page"""
        self.path_field.fill(path)
        self.connect_btn.click()

    # pylint: disable=no-self-use
    def prerequisite(self):
        """Page prerequisite used by navigator"""
        return WizardProductView

    @property
    def is_displayed(self):
        return self.path_field.is_displayed and WizardCommonView.is_displayed and \
               self.endpoint_path in self.browser.url and self.connect_btn.is_displayed


class WizardRequestView(WizardCommonView, Navigable):
    """
    Representation of Wizard Request view page object.
    """
    endpoint_path = '/p/admin/onboarding/wizard/request/new'
    method_field = TextInput(id='request_path')
    send_request_btn = ThreescaleSubmitButton()
    request_example_path = Text(locator='//*[@id="edit_request_2"]/ol/li[1]/code/span[2]')
    backend_url_example = Text(locator='//*[@id="edit_request_2"]/ol/li[2]/code/span[1]')
    feedback_example_path = Text(locator='//*[@id="edit_request_2"]/ol/li[2]/code/span[2]')
    edit_api_btn = Button(locator="//a[@href='/p/admin/onboarding/wizard/api/edit']")

    @step('WizardResponseView')
    def send_request(self):
        """Press send request button"""
        self.send_request_btn.click()

    # pylint: disable=no-self-use
    def prerequisite(self):
        """Page prerequisite used by navigator"""
        return WizardConnectView

    @property
    def is_displayed(self):
        return self.method_field.is_displayed and WizardCommonView.is_displayed and \
               self.endpoint_path in self.browser.url and self.edit_api_btn.is_displayed


class WizardResponseView(WizardCommonView, Navigable):
    """
    Representation of Wizard Request view page object.
    """
    endpoint_path = '/p/admin/onboarding/wizard/request'
    page_title = Text("//main/h1")
    what_next_btn = Button(locator="//a[@href='/p/admin/onboarding/wizard/outro']")
    base_url = TextInput(id='request_api_base_url')
    try_again_btn = Link('//*[@id="edit_request_2"]/fieldset/ol/input')

    # pylint: disable=no-self-use
    def prerequisite(self):
        """Page prerequisite used by navigator"""
        return WizardRequestView

    def try_again(self, url):
        """Fill backend api url with 'url' and click to navigate to next page"""
        self.base_url.fill(url)
        self.try_again_btn.click()

    @step('WizardOutroView')
    def next_page(self):
        """Proceed to next page"""
        self.what_next_btn.click()

    @property
    def is_displayed(self):
        return self.endpoint_path in self.browser.url and self.what_next_btn.is_displayed \
               and WizardCommonView.is_displayed


class WizardOutroView(WizardCommonView, Navigable):
    """
    Representation of Wizard outro view page object.
    """
    endpoint_path = '/p/admin/onboarding/wizard/outro'

    continue_button = Link("/html/body/main/a")
    page_title = Text("//main/h1")

    def next_page(self):
        """Proceed to next page"""
        self.continue_button.click()

    # pylint: disable=no-self-use
    def prerequisite(self):
        """Page prerequisite used by navigator"""
        return WizardResponseView

    @property
    def is_displayed(self):
        return self.endpoint_path in self.browser.url and self.continue_button.is_displayed \
               and WizardCommonView.is_displayed
