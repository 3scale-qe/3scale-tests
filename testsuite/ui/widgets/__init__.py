""" 3scale specific widgets"""

import backoff
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from widgetastic.exceptions import NoSuchElementException
from widgetastic.utils import ParametrizedLocator
from widgetastic.widget import GenericLocatorWidget, Widget
from widgetastic.widget import TextInput
from widgetastic.xpath import quote
from widgetastic_patternfly4 import Select

from testsuite.ui.exception import ItemNotPresentException


# Widget contains fill method which raise not implemented exception if widget is not fillable but pylint detect it as
# an abstract method. Disabling abstract-method for all widgets.
# pylint: disable=abstract-method


class RadioGroup(GenericLocatorWidget):
    """
    Radio group of 3scale pages.
    """

    OPTIONS_SECTION_CLASS = '//fieldset/ol[contains(@class, "{}")]'
    OPTIONS_SECTION = "/fieldset/ol"

    OPTIONS = "./li"
    OPTIONS_INPUT = OPTIONS + "/label/input"
    OPTIONS_BY_ID = OPTIONS_INPUT + '[@id="{}"]'

    def __init__(self, parent=None, locator=None, field_set_identifier="", logger=None):
        super().__init__(parent, locator, logger)
        if field_set_identifier:
            self.locator = locator + self.OPTIONS_SECTION_CLASS.format(field_set_identifier)
        else:
            self.locator = locator + self.OPTIONS_SECTION

    def select(self, option: str):
        """
        Select radio element from the list.
        :param option: String id-s of options
        """
        element = self.browser.element(self.OPTIONS_BY_ID.format(option))
        element.click()

    # pylint: disable=arguments-differ
    def read(self):
        """
        Read the selected option
        """
        options = self.browser.elements(self.OPTIONS_INPUT)
        for option in options:
            if option.is_selected():
                return option.get_dom_attribute("id")
        return None


class CheckBoxGroup(GenericLocatorWidget):
    """
    CheckBox group of 3scale pages
    :param ol_identifier: Set if Checkbox group is identified by attribute in ol tag.
                     e.g. fieldset/ol[class=ServiceList]
    :param field_set_identifier: Set if Checkbox group identifier is in fieldset level of group.
    """

    OPTIONS_SECTION = "/fieldset/ol"
    OPTIONS_SECTION_OL_CLASS = '//fieldset/ol[contains(@class, "{}")]'

    OPTIONS = "./li"
    OPTIONS_INPUT = OPTIONS + "/label/input"
    OPTIONS_BY_ID = OPTIONS_INPUT + '[@id="{}"]'
    OPTIONS_BY_TEXT = OPTIONS + '/label[normalize-space(.)="{}"]/input'

    # pylint: disable=too-many-arguments
    def __init__(self, parent=None, locator=None, ol_identifier=None, logger=None):
        super().__init__(parent, locator, logger)
        if ol_identifier:
            self.locator = locator + self.OPTIONS_SECTION_OL_CLASS.format(ol_identifier)
        else:
            self.locator = locator + self.OPTIONS_SECTION

    def is_checked(self, option: str):
        """Detect if checkbox is already checked"""
        element = self.browser.element(self.OPTIONS_BY_ID.format(option))
        return element.is_selected()

    def check(self, options: list):
        """
        Uncheck all checkboxes of the group
        Selects check box element from the list.
        :param options: List of string id-s of options
        """
        self.clear_all()
        for option in options:
            element = self.browser.element(self.OPTIONS_BY_ID.format(option))
            if not element.is_selected():
                element.click()

    def check_by_text(self, options: list):
        """
        Uncheck all checkboxes of the group
        Selects check box element from the list.
        :param options: List of string id-s of options
        """
        self.clear_all()
        for option in options:
            element = self.browser.element(self.OPTIONS_BY_TEXT.format(option))
            if not element.is_selected():
                element.click()

    def uncheck(self, options: list):
        """
        Unselect check box element from the list.
        :param options: List of string id-s of options
        """
        for option in options:
            element = self.browser.element(self.OPTIONS_BY_ID.format(option))
            if element.is_selected():
                element.click()

    def clear_all(self):
        """
        Unset all option in checkbox group.
        """
        for element in self.browser.elements(self.OPTIONS):
            if element.is_selected():
                element.click()


class ThreescaleDropdown(GenericLocatorWidget):
    """Specific dropdown of 3scale pages"""

    def selected_value(self):
        """Return selected attribute from dropdown"""
        return self.browser.selenium.find_element(By.XPATH, "//select/option[@selected='selected']").get_attribute(
            "value"
        )

    def select_by_value(self, value):
        """Select given value from dropdown"""
        if value:
            self.browser.selenium.find_element(By.XPATH, f"//select/option[@value='{value}']").click()

    def select_by_text(self, text):
        """Select given text from dropdown"""
        self.browser.selenium.find_element(By.XPATH, f"//select/option[normalize-space(.)='{text}']").click()


class ThreescaleCheckBox(GenericLocatorWidget):
    """Specific CheckBox button of 3scale pages"""

    def check(self, value=True):
        """Check or uncheck 3scale checkbox"""
        if value != self.is_checked():
            self.__element__().click()

    def is_checked(self):
        """
        :return if checkbox is checked
        """
        return self.__element__().get_attribute("checked") == "true"


class PolicySection(Widget):
    """Widget representing Policies table section"""

    ROOT = "//div[@class='PoliciesWidget']/section"
    POLICY_LIST = ".//ul/li"
    REGISTRY_ITEMS_LOCATOR = "//ul/li/article/h3"
    REGISTRY_ITEM_LOCATOR = "//ul/li/article/h3[text()='{}']"
    CHAIN_ITEMS_LOCATOR = ".//ul/li//article/h3"
    CHAIN_ITEM_LOCATOR = "//ul/li//article/h3[text()='{}']"
    ADD_POLICY_LOC = ".//button[normalize-space(.)='Add policy']"

    def __init__(self, parent=None, logger=None):
        Widget.__init__(self, parent, logger=logger)

    @property
    def items(self):
        """Returns a list of all policy registry items as strings."""
        return [self.browser.text(el) for el in self.browser.elements(self.CHAIN_ITEMS_LOCATOR, parent=self)]

    @property
    def registry_items(self):
        """Returns a list of all policy registry items as strings."""
        return [self.browser.text(el) for el in self.browser.elements(self.REGISTRY_ITEMS_LOCATOR)]

    @property
    def is_policy_registry_displayed(self):
        """Check if policy registry list is displayed.
        :return: True if displayed, False otherwise.
        """
        return self.browser.is_displayed(self.ADD_POLICY_LOC)

    @property
    def first_policy(self):
        """
        Get the name of the first policy in the policy chain.
        :return: Name of the policy
        """
        return self.browser.text(self.browser.element(self.CHAIN_ITEMS_LOCATOR, parent=self))

    def add_policy(self, policy_name):
        """Opens the Policy registry list and adds a policy by its name.
        :param policy_name: Name of the policy to be added
        """
        self.browser.click(self.ADD_POLICY_LOC, parent=self)
        self.add_item(policy_name)

    def edit_policy(self, policy_name):
        """
        :param policy_name:
        """
        if self.has_item(policy_name):
            self.item_select(policy_name)
        else:
            raise ItemNotPresentException("Item {!r} not found.".format(policy_name))

    def drag_and_drop_policy(self, source, destination):
        """Drag and drop element from source element to destination,
        builtin drag_and_drop function is not working hence this workaround.
        :param
            source: string : name of source Policy
            destination: string : name of destination Policy
        """
        ac = ActionChains(self.browser.selenium)
        ac.click_and_hold(self.browser.element("./ul/li//article/h3[text()='{}']/../p/span".format(source)))
        ac.move_to_element(self.browser.element("./ul/li//article/h3[text()='{}']/../p/span".format(destination)))
        ac.release(self.browser.element("./ul/li//article/h3[text()='{}']/../p/span".format(destination)))
        ac.perform()

    def has_item(self, item):
        """Returns whether the items exists.
        :param
            item: item name
        :return:
            Boolean - True if present, False if not.
        """
        return item in self.items

    # pylint: disable=raise-missing-from
    def item_element(self, item):
        """Returns a WebElement for given item name.
        :return WebElement
        """
        try:
            return self.browser.element(self.CHAIN_ITEM_LOCATOR.format(item), parent=self)
        except NoSuchElementException:
            raise ItemNotPresentException("Item {!r} not found.".format(item))

    # pylint: disable=raise-missing-from
    def add_item(self, item):
        """Add policy from policy registry"""
        self.logger.info("Selecting %r", item)
        if item not in self.registry_items:
            raise ItemNotPresentException('Item "{item}" of policy is not present'.format(item=item))
        self.browser.click(self.item_element(item))

    def item_select(self, item):
        """Opens the Policy registry and selects the desired policy.
        :param
            item: Item to be selected
        """
        self.logger.info("Selecting %r", item)
        if not self.has_item(item):
            raise ItemNotPresentException('Item "{item}" of policy is not present'.format(item=item))
        self.browser.click(self.item_element(item))


class APIDocsSelect(Select):
    """Specific select for 3scale API doc page"""

    def item_select(self, item):
        # This is for opening the menu because the locator matches all buttons and Select doesn't work
        element = self.browser.element("//button[@aria-label='Options menu']")
        element.click()
        super().item_select(item)


class DivBasedEditor(TextInput):
    """Widget of Div Based editor used to load Active doc specification"""

    def fill(self, value, sensitive=False):
        """Fill value to Div Based Editor"""
        self.browser.click(self)
        self.browser.send_keys_to_focused_element(value)


class ActiveDocV2Section(Widget):
    """Active Doc V2 preview section"""

    ROOT = ParametrizedLocator('//*[@id="default_endpoint_list"]')
    ENDPOINTS_LIST = "./li"
    ITEMS_LOCATOR = "./li/ul/li/div/h3/span[2]/a"
    ITEMS_BUTTON_LOCATOR = './li/ul/li/div/h3/span[2]/a[text()="{}"]/ancestor::li/div[2]/form/div/input'
    RESPONSE_CODE_LOCATOR = './/*[contains(@class, "response_code")]/pre'

    def __init__(self, parent=None, logger=None):
        Widget.__init__(self, parent, logger=logger)

    @property
    def endpoints(self):
        """Returns a list of all endpoints registry items as strings."""
        return [self.browser.text(el) for el in self.browser.elements(self.ITEMS_LOCATOR, parent=self)]

    def item_element(self, item):
        """Returns a WebElement for given item name.
        :return WebElement
        """
        try:
            return self.browser.element(self.ITEMS_BUTTON_LOCATOR.format(item), parent=self)
        except NoSuchElementException as exc:
            raise NoSuchElementException("Item {!r} not found.".format(item)) from exc

    @backoff.on_exception(backoff.fibo, NoSuchElementException, max_tries=4, jitter=None)
    def try_it_out(self, method):
        """Make test request
        :param method string eg. /post, /get
        """
        self.browser.click(self.item_element(method))

    @backoff.on_exception(backoff.fibo, NoSuchElementException, max_tries=4, jitter=None)
    def get_response_code(self):
        """Return response code called by method try_it_out"""
        return self.browser.text(self.RESPONSE_CODE_LOCATOR, parent=self)


class ThreescaleAnalyticsDropdown(GenericLocatorWidget):
    """Specific Dropdown menu of 3scale analytics pages"""

    def select(self, value):
        """Select specific metric to be displayed"""
        self.wait_displayed()
        self.click()
        self.browser.selenium.find_element(By.XPATH, f"//*[text()='{value}']").click()

    def text(self):
        """Get text of metric"""
        self.wait_displayed()
        return self.browser.element(self.locator).text


class ThreescaleButtonGroup(GenericLocatorWidget):
    """Specific Button Group of 3scale pages"""

    SELECTED = "./a[1]"
    DROPDOWN_ITEMS = "./ul/li/a"
    DROPDOWN_TOGGLE = "./a[2]"

    def __init__(self, parent=None, locator="", logger=None):
        super().__init__(parent=parent, locator=locator, logger=logger)

    def select(self, option):
        """Select button from button group"""
        button = self.browser.element(self.SELECTED)
        if button.get_dom_attribute("href") == option:
            button.click()
            return
        items = self.browser.elements(self.DROPDOWN_ITEMS)
        for item in items:
            if item.get_dom_attribute("href") == option:
                self.browser.element(self.DROPDOWN_TOGGLE).click()
                item.click()
                return


class HorizontalNavigation(Widget):
    """
    Represents the PatternFly horizontal navigation

    https://www.patternfly.org/v4/components/navigation#horizontal-subnav
    """

    ROOT = ParametrizedLocator("{@locator}")
    LOCATOR_START = './/nav[@class="pf-c-nav pf-m-horizontal pf-m-tertiary"]'
    ITEMS = "./ul/li/[self::a or self::button]"
    ITEM_MATCHING = "./ul/li/a[contains(normalize-space(.), {})]"

    def __init__(self, parent=None, locator=None, logger=None):
        super().__init__(parent, logger=logger)

        if locator:
            self.locator = locator
        else:
            self.locator = self.LOCATOR_START

    def select(self, item):
        """Selects an item in the navigation."""
        self.logger.info("Selecting %r in vertical navigation", item)
        item = self.browser.element(self.ITEM_MATCHING.format(quote(item)))
        item.click()


class ThreescaleDeleteEditGroup(GenericLocatorWidget):
    """Special Delete Edit group for 3scale"""

    DELETE_LOCATOR = ".//button[contains(@class, delete)]"
    EDIT_LOCATOR = ".//a[@title='Edit']"

    def __init__(self, parent=None, locator=".//*[@class='pf-c-overflow-menu']", logger=None):
        super().__init__(parent=parent, locator=locator, logger=logger)

    def delete(self):
        """Click on delete button"""
        self.browser.element(self.DELETE_LOCATOR).click()

    def edit(self):
        """Click on edit button"""
        self.browser.element(self.EDIT_LOCATOR).click()
