"""Plug-in for Widgetastic browser with 3scale specific environment settings"""

from datetime import datetime
import os
from urllib import parse
from time import sleep
from widgetastic.browser import Browser, DefaultPlugin


# pylint: disable=abstract-method
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
        if self.browser.browser_type == 'firefox':
            sleep(1)
        pass


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

    def take_screenshot(self, error_type):
        """
        Take screen shot from the current browser window.

        This method is called automatically in case any exception during UI
        session happens.
        """
        now = datetime.now()
        if os.environ.get('resultsdir') is not None:
            path = os.environ['resultsdir']
        else:
            path = "./test-run-results"
        if not os.path.exists(path):
            os.makedirs(path)
        filename = '{0}-screenshot-{1}.png'.format(
            error_type,
            now.strftime('%Y-%m-%d_%H:%M:%S')
        )
        path = os.path.join(path, filename)
        self.selenium.save_screenshot(path)
