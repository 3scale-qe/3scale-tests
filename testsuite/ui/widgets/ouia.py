"""Widgets that extends OUIAGenericWidget"""
from logging import Logger
from typing import Optional

from selenium.webdriver.common.by import By
from widgetastic.types import ViewParent
from widgetastic_patternfly4.navigation import check_nav_loaded
from widgetastic_patternfly4 import ouia


# pylint: disable=abstract-method


class Navigation(ouia.Navigation):
    """
    Navigation menu for 3scale Views (menu on the left side of Audience, Product, Backend and Settings Views).
    widgetastic_patternfly4.Navigation was extended because it does not support item selection based on href
    which brought great code simplification for this component.

    As part of NavViews it handles steps to particular views. When `select_href` method is called with `href`
    argument (this argument is usually taken from destination View in a form of `path` variable),
    it finds right elements in Navigation, expands parent item if necessary and clicks correct item.
    """

    RELATED_RESOURCE = '//div[@class="pf-c-nav__current-api"]'
    HREF_LOCATOR = './section/ul/li/a[@href="{}"]'

    def __init__(
        self,
        parent: ViewParent = None,
        component_id: str = "OUIA-Generated-Nav-1",
        logger: Optional[Logger] = None,
        **kwargs,
    ) -> None:
        super().__init__(
            parent=parent,
            component_id=component_id,
            logger=logger,
            **kwargs,
        )

    @check_nav_loaded
    def select_href(self, href):
        """
        Selects item from Navigation with specific href locator
        """
        for element in self.browser.elements("./ul/li"):
            if "pf-m-expandable" in element.get_attribute("class").split():
                nav_item = self.browser.elements(self.HREF_LOCATOR.format(href), parent=element)
                if nav_item:
                    if "pf-m-expanded" not in element.get_attribute("class").split():
                        self.browser.click(element)
                        self.browser.wait_for_element(self.HREF_LOCATOR.format(href), parent=element, visible=True)
                    self.browser.click(nav_item[0])
                    return
            else:
                nav_item_href = element.find_element(By.TAG_NAME, "a").get_attribute("href")
                if nav_item_href.endswith(href):
                    self.browser.click(element)
                    return

    def nav_resource(self):
        """
        Returns navigation title. This text is shown only in Product and Backend Views and it is used
        in `is_display` method to verify, if currently visible navigation menu (or whole View)
        is correctly loaded for particular Product or Backend.
        """
        return self.browser.element(self.RELATED_RESOURCE).text
