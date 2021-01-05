""" 3scale specific widgets"""

from widgetastic.widget import (
    Text, GenericLocatorWidget)
from widgetastic_patternfly4 import ContextSelector, Navigation


# pylint: disable=arguments-differ
from widgetastic_patternfly4.navigation import check_nav_loaded


class Link(Text):
    """b
    Clickable/readable link representation accessible via the standard view functions read/fill.
    """

    def fill(self, value):
        if value:
            self.browser.click(self)


# pylint: disable=abstract-method
class RadioGroup(GenericLocatorWidget):
    """
    Radio group of 3scale pages. It contains both radio and check box elements, therefore it is not
    typical radio element. No control of option switching is implemented.

    In case of check box (like one on the bottom of the User Edit page), user needs to remember that
    possibility of multiple selected options is allowed (not an typical radio behaviour)
    """
    OPTIONS_SECTION = './fieldset/ol[contains(@class, "{}")]'

    OPTIONS = './li'
    OPTIONS_BY_ID = OPTIONS + '/label/input[@id="{}"]'

    def __init__(self, parent, locator, fieldset_id="", logger=None):
        super().__init__(parent, locator, logger)
        self.options_section = self.browser.element(self.OPTIONS_SECTION.format(fieldset_id))

    def select(self, *options):
        """
        Select radio (check box) element from the list.
        :param options: String id-s of options
        """
        for option in options:
            element = self.browser.element(self.OPTIONS_BY_ID.format(option), parent=self.options_section)
            self._select_option(element)

    def clear_all(self):
        """
        Unset all option in radiogroup.
        """
        for element in self.browser.elements(self.OPTIONS, parent=self.options_section):
            self._select_option(element)

    @staticmethod
    def _select_option(element):
        if 'is-unchecked' in element.get_attribute("class").split():
            element.click()


# pylint: disable=too-many-ancestors
class ContextMenu(ContextSelector):
    """
    ContextMenu that extends ContextSelector lactated in Widgetastic PF4 libraries, but briefly adjusted
    to fit 3scale needs.
    """
    ROOT = './/div[contains(@class, "PopNavigation--context")]'
    DEFAULT_LOCATOR = './/div[contains(@class, "PopNavigation--context")]'
    BUTTON_LOCATOR = './/a[@href="#context-menu"]'

    ITEMS_LOCATOR = ".//ul[@class='PopNavigation-list']/li"
    ITEM_LOCATOR = (
        ".//*[contains(@class, 'PopNavigation-listItem')"
        " and normalize-space(.)={}]"
    )


# pylint: disable=abstract-method
class NavigationMenu(Navigation):
    """
    Navigation menu for 3scale Views (menu on the left side of Audience, Product, Backend and Settings Views).
    widgetastic_patternfly4.Navigation was extended because it does not support item selection based on href
    which brought great code simplification for this component.

    As part of NavViews it handles steps to particular views. When `select_href` method is called with `href`
    argument (this argument is usually taken from destination View in a form of `endpoint_path` variable),
    it finds right elements in Navigation, expands parent item if necessary and clicks correct item.
    """
    LOCATOR_START = './/nav[contains(@class, "pf-c-nav"){}]'
    ITEMS = "./ul/li[.//*[self::a or self::button]]"
    SUB_ITEMS = './section/ul/li[contains(@class, "pf-c-nav__item")]'
    HREF_LOCATOR = SUB_ITEMS + '/a[contains(@href, "{}")]'

    @check_nav_loaded
    def select_href(self, href):
        """
        Selects item from Navigation with specific href locator
        TODO: Add an exception like in Navigation select method
        """
        for element in self.browser.elements(self.ITEMS):
            item = self.browser.elements(self.HREF_LOCATOR.format(href), parent=element)
            if item:
                if "pf-m-expanded" not in element.get_attribute("class").split():
                    self.browser.click(element)
                self.browser.click(item[0])
                return
