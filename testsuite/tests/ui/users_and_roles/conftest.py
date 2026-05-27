"""Conftest for user permissions tests"""

import pytest
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from widgetastic.widget import GenericLocatorWidget


@pytest.fixture
def is_page_accessible():
    """
    Helper function for permission tests to check if a page is accessible.

    This checks for successful page access by verifying:
    1. Correct URL path is loaded
    2. The masthead header is present (exists on all allowed pages, not on access denied)
    """

    def _check(page):
        if page.path not in page.browser.url:
            return False

        try:
            masthead = GenericLocatorWidget(
                page, locator="//header[contains(@class, 'pf-c-masthead') and contains(@class, 'pf-m-display-inline')]"
            )
            if not masthead.is_displayed:
                return False
        except (NoSuchElementException, WebDriverException):
            return False

        return True

    return _check
