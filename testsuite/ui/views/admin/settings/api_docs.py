"""
View representations of 3scale API Docs pages
"""

import backoff
from widgetastic.exceptions import NoSuchElementException
from widgetastic.widget import Text, ParametrizedView, ParametrizedLocator, View, TextInput
from widgetastic_patternfly4 import Button

from testsuite.ui.views.admin.settings import BaseSettingsView


class _Endpoint(ParametrizedView):
    """
    Parametrized View that represents a section (for example "Service Read") in API Docs
    """
    PARAMETERS = ('endpoint_name',)
    ROOT = ParametrizedLocator('//a[text()={endpoint_name|quote}]/ancestor::li[contains(@class, "operation")]')
    ALL_ENDPOINTS = './/a[@class="toggle"]'
    name = Text(locator='.//a[@class="toggle"]')
    access_token = TextInput(name='access_token')
    submit_button = Button(locator='.//button[@class="submit"]')
    status_code_field = Text(locator='.//div[@class="block response_code"]/pre')

    def unroll(self):
        """Unrolls the endpoint section"""
        if not self.submit_button.is_displayed:
            self.name.click()
            self.submit_button.wait_displayed()

    def status_code(self):
        """Returns request status code"""
        self.status_code_field.wait_displayed()
        return self.status_code_field.read()

    def get_param(self, param):
        """Returns input param field"""
        return self.browser.element(f'.//input[contains(@data-threescale-name, "{param}")]')

    def fill(self, values: dict):
        """
        Widgetastic fill method override. Fills Parameter values for API doc endpoint
        Args:
            :param values: dict of param_name:param_value
        """
        self.unroll()
        for param in values:
            self.get_param(param).send_keys(values.get(param))

    def send_request(self, params: dict):
        """
        Wraps basic use case for API docs endpoint. Fills endpoint params, sends request and returns response code
        Args:
            :param params: dict of param_name:param_value
            :return response code
        """
        self.fill(params)
        self.submit_button.click()
        return self.status_code_field.read()

    @classmethod
    def all(cls, browser):
        """Override of parent class `all` method"""
        return [(browser.text(el),) for el in browser.elements(cls.ALL_ENDPOINTS)]


class APIDocsView(BaseSettingsView):
    """
    View representation of API Docs page
    """
    path_pattern = '/p/admin/api_docs'
    page_title = Text(locator='//*[@id="content"]/h1')
    service_management_api_category = Text(locator='//*[@data-name="service_management_api"]')
    account_management_api_category = Text(locator='//*[@data-name="account_management_api"]')
    policy_registry_api_category = Text(locator='//*[@data-name="policy_registry_api"]')
    endpoint = View.nested(_Endpoint)

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

    def prerequisite(self):
        return BaseSettingsView

    @backoff.on_predicate(backoff.fibo, lambda x: x < 200, max_tries=8)
    def post_navigate(self, **kwargs):
        """
        APIDocsView loads Endpoints dynamically with js script.
        Once navigated to this View, Navigator waits for all API endpoint sections to be loaded.
        """
        return len(self.endpoint)

    @property
    def is_displayed(self):
        return BaseSettingsView.is_displayed.fget(self) \
               and self.path in self.browser.url \
               and self.page_title.is_displayed \
               and self.service_management_api_category.is_displayed \
               and self.account_management_api_category.is_displayed \
               and self.policy_registry_api_category.is_displayed \
               and self.page_title.text == "3scale API Documentation"
