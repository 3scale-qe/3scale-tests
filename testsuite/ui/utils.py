"""
    This file contains utilities that can be used across the tests to help wit the certain tasks. (ui helpers)
"""


def assert_displayed_in_new_tab(browser, new_tab_opener, view_class):
    """
        Opens the website in the new tab and checks if it is displayed.
        If "wait" is set to true, it will also trigger a function THAT IS PRESENT ONLY IN SPECIFIC CLASSES in order to
        wait for the website to be loaded by refreshing it. (Example -> LandingView)
    """
    with browser.new_tab(new_tab_opener):
        view = view_class(browser)
        assert view.is_displayed
