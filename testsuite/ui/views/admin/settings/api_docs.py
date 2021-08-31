"""
View representations of 3scale API Docs pages
"""
from widgetastic.exceptions import NoSuchElementException
from widgetastic.widget import Text, ParametrizedView, ParametrizedLocator
from widgetastic_patternfly4 import Button

from testsuite.ui.views.admin.settings import BaseSettingsView


class APIDocsView(BaseSettingsView):
    """
        View representation of API Docs page
    """
    path_pattern = '/p/admin/api_docs'
    page_title = Text(locator='//*[@id="content"]/h1')
    service_management_api_category = Text(locator='//*[@data-name="service_management_api"]')
    account_management_api_category = Text(locator='//*[@data-name="account_management_api"]')
    policy_registry_api_category = Text(locator='//*[@data-name="policy_registry_api"]')

    def get_id_input_by_name(self, name):
        """
            Helper method for autocomplete part of a test that tests "Service Read"
            (it finds the correct autocorrect text and returns its ID)
        """
        auto_complete_part = '//*[@id="content"]/div/div[13]/ul/li'
        for li_index in range(len(self.browser.elements(auto_complete_part))):
            if self.browser.element(auto_complete_part + f'[{li_index + 1}]/strong').text == name:
                return self.browser.element(auto_complete_part + f'[{li_index + 1}]/span')
        raise NoSuchElementException('No element was found')

    # pylint: disable=abstract-method, disable=invalid-name
    class endpoint_section(ParametrizedView):
        """
            Parametrized View that represents a section (for example "Service Read") in API Docs

            //*[@id="account_management_api_endpoint_operations"]/li[177]/div[2]
        """
        PARAMETERS = ('endpoint_name',)
        ROOT = ParametrizedLocator('//a[text()={endpoint_name|quote}]/ancestor::li[@class="get operation"]')
        name = Text(locator='.//a[@class="toggle"]')
        submit_button = Button(locator='.//button[@class="submit"]')
        status_code = Text(locator='.//div[@class="block response_code"]/pre')

        def unroll(self):
            """
                unrolls the section, so we can start working with the section
            """
            if not self.submit_button.is_displayed:
                self.name.click()
                self.submit_button.wait_displayed()

        def get_input_field(self, key):
            """
                returns input field for a form part that was provided (for example, if we pass it "access_token",
                we will receive the input field, where we can type the access token).
            """
            return self.browser.element(f'.//input[contains(@data-threescale-name, "{key}")]')

        def fill_input(self, key, value):
            """
                gets the required input field and fills it up
            """
            self.get_input_field(key).send_keys(value)

    def prerequisite(self):
        return BaseSettingsView

    @property
    def is_displayed(self):
        return BaseSettingsView.is_displayed.fget(self) \
               and self.path in self.browser.url \
               and self.page_title.is_displayed \
               and self.service_management_api_category.is_displayed \
               and self.account_management_api_category.is_displayed \
               and self.policy_registry_api_category.is_displayed \
               and self.page_title.text == "3scale API Documentation"
