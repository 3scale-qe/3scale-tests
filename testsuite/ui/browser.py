"""Plug-in for Widgetastic browser with 3scale specific environment settings"""
from contextlib import contextmanager
from time import sleep
from urllib import parse

from widgetastic.browser import Browser, DefaultPlugin


class ThreescaleBrowserPlugin(DefaultPlugin):
    """
    Plug-in for :class:`ThreeScaleBrowser` which make sure page is loaded completely and is safe for UI interacting.
    """

    ENSURE_PAGE_SAFE = '''
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
        '''

    def ensure_page_safe(self, timeout='15s'):
        """
        Ensures page is fully loaded.
        Default timeout was 10s, this changes it to 15s.
        """
        super().ensure_page_safe(timeout)

    def before_click(self, element, locator=None):
        """
        Invoked before clicking on an element. Ensure page is fully loaded
        before clicking.
        This method implements simple even listener, that listens for unload event that indicates
        navigation to a new page.
        """
        if self.browser.browser_type == 'firefox':
            listener = '''
            window.addEventListener("beforeunload", function() {
                console.log("Navigating to a new page. Unloading the window.");
                localStorage.setItem("pageUnloading", true);
            });
            '''
            self.browser.execute_script(listener)

    def after_click(self, element, locator=None):
        """
        Invoked after clicking on an element. Ensure page is fully loaded
        before proceeding further.
        When navigation to a new page Firefox does not change state of `document.readyState` immediately.
        This method uses simple sleep when navigating to a new page with Firefox browser.
        """
        if self.browser.browser_type == 'firefox':
            if not self.browser.alert_present:
                unloading = self.browser.execute_script('return localStorage.getItem("pageUnloading") == "true";')
                if unloading:

                    sleep(2)
                    self.browser.execute_script('localStorage.setItem("pageUnloading", false);')
                    self.ensure_page_safe()


# pylint: disable=abstract-method
class ThreeScaleBrowser(Browser):
    """Wrapper around :class:`widgetastic.browser.Browser`"""

    def __init__(self, selenium, session=None, extra_objects=None):
        """Pass webdriver instance, session and other extra objects (if any).

        :param selenium: :class:`selenium.WebDriver`
            instance.
        :param session: :class:`threescale.session.Session` instance.
        :param extra_objects: any extra objects you want to include.
        """
        extra_objects = extra_objects or {}
        extra_objects.update({'session': session})
        super().__init__(
            selenium,
            plugin_class=ThreescaleBrowserPlugin,
            extra_objects=extra_objects)
        self.window_handle = selenium.current_window_handle

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
