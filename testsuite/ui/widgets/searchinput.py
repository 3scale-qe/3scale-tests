"""Basic implementation of widgetastic widget for PatternFly4 search-input"""

from widgetastic.widget import GenericLocatorWidget, TextInput


class BaseSearchInput:
    """Basic representation of the Patternfly4 search-input
    (this if not feature complete)

    https://www.patternfly.org/v4/components/search-input/
    """

    INPUT_LOCATOR = ".//input[@aria-label='Search input']"
    BUTTON_LOCATOR = ".//button[contains(@aria-label,'Search')]"

    text_input = TextInput(locator=INPUT_LOCATOR)
    button = GenericLocatorWidget(locator=BUTTON_LOCATOR)

    def fill(self, value):
        """Set the search string"""
        self.text_input.fill(value)

    def search(self):
        """Submit the searching"""
        self.button.click()

    def fill_and_search(self, value):
        """Enter the search string and hit Search button"""
        self.fill(value)
        self.search()


class SearchInput(BaseSearchInput, GenericLocatorWidget):
    """The widget for patternfly4 search-input"""


class ThreescaleSearchInput(SearchInput):
    """Threescale specific widget with default locator"""

    def __init__(self, *args, locator=".//div[contains(@class, 'pf-m-search-filter')]", **kwargs):
        super().__init__(*args, locator, **kwargs)
