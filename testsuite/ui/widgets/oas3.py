"""Widgets used by OAS3"""
from selenium.webdriver.common.by import By
from widgetastic.utils import ParametrizedLocator
from widgetastic.widget import ParametrizedView, Text, Table, Widget, TextInput, GenericLocatorWidget


# pylint: disable=abstract-method


class OAS3DropDown(Widget):
    """DropDown element used by OAS3. Usually used for key selection or autocomplete function"""

    EXPAND = ".//select"
    OPTION = './/select/option[contains(text(),"{}")]'

    def __init__(self, parent=None, locator='.//div[@class="examples-select"]', logger=None):
        super().__init__(parent, locator=locator, logger=logger)
        self.locator = locator

    def select_item(self, value):
        """Selects item by their respective values in the select"""
        item = self.OPTION.format(value)
        self.browser.selenium.find_element(By.XPATH, item).click()

    def __locator__(self):
        return self.locator

    def __repr__(self):
        return "{}{}".format(type(self).__name__, self.locator)


class Endpoint(ParametrizedView):
    """
    Parametrized View that represents a section (for example "Service Read") in API Docs
    """

    PARAMETERS = ("endpoint_method", "endpoint_path")
    ROOT = ParametrizedLocator(
        "//span[@data-path={endpoint_path|quote}]/.."
        "/span[text()={endpoint_method|quote}]"
        '/ancestor::div[contains(@id, "operations")]'
    )
    ALL_ENDPOINTS = './/div[@class="operation-tag-content"]/span'

    method = Text(locator='.//span[@class="opblock-summary-method"]')
    path = Text(locator='.//span[@class="opblock-summary-path"]')
    try_out_btn = GenericLocatorWidget(locator='.//button[@class="btn try-out__btn"]')
    execute_btn = GenericLocatorWidget(locator=".//button[contains(@class, 'btn execute')]")
    parameters = Table('.//table[@class="parameters"]')
    response = Table('.//table[@class="responses-table live-responses-table"]')

    @property
    def expanded(self):
        """Returns True if endpoint section is expanded"""
        return "is-open" in self.__element__().get_attribute("class")

    @property
    def status_code(self):
        """Returns request status code"""
        self.response.wait_displayed()
        return self.response[0].code.text

    def expand_item(self):
        """Expands endpoint section"""
        if not self.expanded:
            self.browser.click(self)

    def execute(self, params: dict[str, str] = None):
        """
        Executes request to this endpoint by performing few steps (if required or necessary):
            - Expands current endpoint section
            - Clicks Try Out button
            - Sets the parameters
            - Click Execute button
        """
        self.expand_item()
        if self.try_out_btn.is_displayed:
            self.try_out_btn.click()
        if params:
            for key in params:
                self.set_param(key, params[key])
        self.execute_btn.click()

    def get_param(self, key):
        """Returns value from endpoint parameter from column defined by `key`"""
        self.expand_item()
        return self.parameters.row(name__startswith=key).description

    def set_param(self, key, value):
        """Sets the `value` for the endpoint parameter defined by `key`"""
        self.expand_item()
        column = self.get_param(key)

        select = OAS3DropDown(column)
        text_input = TextInput(column, locator=".//input")
        if select.is_displayed:
            select.select_item(value)
        elif text_input.is_displayed:
            text_input.fill(value)

    @staticmethod
    def extract_text(column):
        """Finds Text Input inside given column and returns its text"""
        return TextInput(column, locator=".//input").value

    @classmethod
    def all(cls, browser):
        """
        Override of parent class `all` method.
        Return list of tuples of all method and path parameters that are necessary to identify ParametrizedView.
        """
        result = []
        for element in browser.elements(cls.ALL_ENDPOINTS):
            endpoint_method = browser.text(browser.element('.//span[@class="opblock-summary-method"]', parent=element))
            endpoint_path = browser.text(browser.element('.//span[@class="opblock-summary-path"]', parent=element))
            result.append((endpoint_method, endpoint_path))
        return result
