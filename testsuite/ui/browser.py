"""Plug-in for Widgetastic browser with 3scale specific environment settings"""

from contextlib import contextmanager
from time import sleep
from urllib import parse
import backoff

from selenium.common.exceptions import NoSuchElementException
from widgetastic.browser import Browser, DefaultPlugin


# pylint: disable=abstract-method
class ThreescaleBrowserPlugin(DefaultPlugin):
    """
    Plug-in for :class:`ThreeScaleBrowser` which make sure page is loaded completely and is safe for UI interacting.
    """

    ENSURE_PAGE_SAFE = """
        function jqueryInactive() {
         return (typeof jQuery === "undefined") ? true : jQuery.active < 1
        }
        function ajaxInactive() {
         return (typeof Ajax === "undefined") ? true :
            Ajax.activeRequestCount < 1
        }
        return {
            jquery: jqueryInactive(),
            ajax: ajaxInactive(),
            document: document.readyState == "complete",
        }
        """

    def ensure_page_safe(self, timeout="15s"):
        """
        Ensures page is fully loaded.
        Default timeout was 10s, this changes it to 15s.
        """
        super().ensure_page_safe(timeout)

    def before_click(self, element, locator=None):
        """
        Invoked before clicking on an element. Ensure page is fully loaded
        before clicking.
        """
        self.ensure_page_safe()

    # pylint: disable=unnecessary-pass
    def after_click(self, element, locator=None):
        """
        Invoked after clicking on an element. Ensure page is fully loaded
        before proceeding further.
        """
        # plugin.ensure_page_safe() is invoked from browser click.
        # we should not invoke it a second time, this can conflict with
        # ignore_ajax=True usage from browser click
        # we need to add sleep in case of using firefox after click action
        # because gecodriver(firefox driver) execute actions in strange way
        # TODO: explore possibilities to check JS running or stalness of
        #  clickable element in click / after_click action
        if self.browser.browser_type == "firefox":
            sleep(1)
        pass


class ThreeScaleBrowser(Browser):
    """Wrapper around :class:`widgetastic.browser.Browser`"""

    def __init__(self, webdriver, session=None, extra_objects=None):
        """Pass webdriver instance, session and other extra objects (if any).
        :param webdriver: :class:`ThreescaleWebdriver` instance.
        :param session: :class:`threescale.session.Session` instance.
        :param extra_objects: any extra objects you want to include.
        """
        extra_objects = extra_objects or {}
        extra_objects.update({"session": session})
        selenium = webdriver.start_session()
        super().__init__(selenium, plugin_class=ThreescaleBrowserPlugin, extra_objects=extra_objects)
        self.window_handle = selenium.current_window_handle
        self.webdriver = webdriver

    def restart_session(self):
        """Restarts browser. Existing webdriver is used"""
        self.webdriver.finalize()
        self.selenium = self.webdriver.start_session()

    def set_path(self, path):
        """Change path for the current browser.url"""
        self.url = parse.urlparse(self.url)._replace(path=path).geturl()

    @contextmanager
    def new_tab(self, trigger, keep_tab=False):
        """
        Context manager for UI operations which result in new tab (window_handle).
        Only one tab wil remain open after this context manager.
        Set `keep_tab` to:
            True - if newly opened tab should be preserved.
            False - if newly opened tab should be closed
        :param trigger: Method that triggers tew tab opening
        :param keep_tab: keep tab flag
        :return: result of the `trigger` method
        """
        old_handles = self.browser.window_handles
        current_handle = self.browser.current_window_handle
        returned_object = trigger()
        new_handle = [t for t in self.browser.window_handles if t not in old_handles][0]
        self.browser.switch_to_window(new_handle)
        self.plugin.ensure_page_safe()
        yield returned_object
        if keep_tab:
            self.browser.close_window(current_handle)
        else:
            self.browser.close_window(new_handle)
            self.browser.switch_to_window(current_handle)

    @backoff.on_exception(backoff.fibo, NoSuchElementException, max_tries=8, jitter=None)
    def switch_to_frame(self, *args, **kwargs) -> None:
        """
        Overrides `switch_to_frame` method defined in widgetastic/browser.
        IFrames for billing (OTP forms) usually take a long time to load. Simple backoff should ensure
        correct frame switching.
        """
        parent = kwargs.pop("parent", self.browser)
        self.selenium.switch_to.frame(self.element(parent=parent, *args, **kwargs))

    def handle_double_alert(self):
        """
        In some user interactions, 3scale displays two alerts to confirm one action. This method confirms both of them.
        Firefox needs a split second between two alerts to load them correctly, so we had to use two similar,
        but different methods defined by Widgetastic:
            `get_alert().accept()` does not implement implicit waiting
            `handle_alert()` waits for an alert to appear, but dismiss all subsequent alerts
        """
        self.get_alert().accept()
        self.handle_alert()
