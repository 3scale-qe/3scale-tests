"""Selenium factory for creating  Threescale browser instances to run UI tests. """

from selenium import webdriver
from msedge.selenium_tools import EdgeOptions
from msedge.selenium_tools.remote_connection import RemoteConnection, EdgeRemoteConnection
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.chrome import ChromeDriverManager
from testsuite.ui.exception import WebDriverError


class SeleniumDriver:
    """
    Selenium driver of desired provider.
    It is also capable of finalizing the browser when it's not needed anymore.

    Usage::
        # init
        driver = SeleniumDriver

        # get factory browser
        browser = driver.get_browser()

        # navigate to desired url
        # [...]

        # perform post-init steps (e.g. skipping certificate error screen)
        driver.post_init()

        # perform your test steps
        # [...]

        # perform factory clean-up
        driver.finalize()
    """

    # pylint: disable=too-many-arguments
    def __init__(self, source, driver, ssl_verify, remote_url=None, binary_path=None):
        """
        Initializes factory with either specified or fetched from settings values.
        :param str source: Browser source name. One of  ('local', 'binary', 'remote')
        :param str driver: Browser name. One of ('chrome', 'firefox')
        :param str ssl_verify: option for certificates ignore
        :param str optional remote_url: URL of remote webdriver
        """
        self.source = source
        self.driver = driver
        self.ssl_verify = ssl_verify
        self.remote_url = remote_url or 'http://127.0.0.1:4444'
        self.binary_path = binary_path
        self.webdriver = None

    # pylint: disable=no-else-return
    def get_driver(self):
        """
        Returns selenium webdriver instance of selected source and browser.

        :return: selenium webdriver instance
        :raises: ValueError: If wrong provider or browser specified.
        """
        if self.source in ('local', 'binary'):
            return self._get_selenium_driver()
        elif self.source == 'remote':
            return self._get_remote_driver()
        else:
            raise ValueError(
                '"{}" browser is not supported. Please use one of {}'
                .format(self.source, ('local', 'remote', 'binary'))
            )

    def post_init(self):
        """
        Perform all required post-init workarounds. Should be
        called _after_ proceeding to desired url.

        :return: None
        """
        # Workaround 'Certificate Error' screen on Microsoft Edge
        if (self.driver == 'edge' and
                ('Certificate Error' in self.webdriver.title or
                 'Login' not in self.webdriver.title)):
            self.webdriver.get(
                "javascript:document.getElementById('invalidcert_continue')"
                ".click()"
            )

        self.webdriver.maximize_window()

    def finalize(self):
        """
        Finalize handling of webdriver.
        :raises: WebDriverError: If problem with browser happens finalization occurs.
        """
        try:
            self.webdriver.quit()
        except Exception as exception:
            raise WebDriverError("Problem with browser finalization") from exception

    def _get_selenium_driver(self):
        """
        Returns selenium webdriver instance of selected browser.
        :note: Should not be called directly, use :meth:get_driver to choose which browser will be used.
        :raises: ValueError: If wrong browser is specified.
        """
        if self.driver == 'chrome':
            options = webdriver.ChromeOptions()
            if not self.ssl_verify:
                options.set_capability("acceptInsecureCerts", True)

            if self.source == 'binary':
                executor = self.binary_path
            elif self.source == 'local':
                executor = ChromeDriverManager().install()
            else:
                raise ValueError(
                    '"{}" source is not supported. Please use one of {}'
                    .format(self.source, ('local', 'binary', 'remote'))
                )

            self.webdriver = webdriver.Chrome(executable_path=executor,
                                              chrome_options=options)
        elif self.driver == 'firefox':
            browser_profile = webdriver.FirefoxProfile()
            if not self.ssl_verify:
                browser_profile.accept_untrusted_certs = True

            if self.source == 'binary':
                executor = self.binary_path
            elif self.source == 'local':
                executor = GeckoDriverManager().install()
            else:
                raise ValueError(
                    '"{}" source is not supported. Please use one of {}'
                    .format(self.source, ('local', 'binary', 'remote'))
                )

            self.webdriver = webdriver.Firefox(firefox_profile=browser_profile,
                                               executable_path=executor)
        else:
            raise ValueError(
                '"{}" webdriver is not supported. Please use one of {}'
                .format(self.driver, ('chrome', 'firefox', 'edge'))
            )
        return self.webdriver

    def _get_remote_driver(self):
        """
        :return:  Returns remote webdriver instance of selected browser
        :note: Should not be called directly, use :meth:get_browser to choose which browser will be used
        """
        if self.driver == 'chrome':
            browser_options = webdriver.ChromeOptions()
            command_executor = RemoteConnection(self.remote_url + '/wd/hub', resolve_ip=False)
        elif self.driver == 'firefox':
            browser_options = webdriver.FirefoxOptions()
            command_executor = RemoteConnection(self.remote_url + '/wd/hub', resolve_ip=False)
        elif self.driver == 'edge':
            browser_options = EdgeOptions()
            browser_options.use_chromium = True
            command_executor = EdgeRemoteConnection(self.remote_url + '/wd/hub')
        else:
            raise ValueError(
                '"{}" webdriver is not supported. Please use one of {}'
                .format(self.driver, ('chrome', 'firefox', 'edge'))
            )

        if not self.ssl_verify and self.driver != 'edge':
            browser_options.set_capability("acceptInsecureCerts", True)

        self.webdriver = webdriver.Remote(
            command_executor=command_executor,
            options=browser_options
        )
        return self.webdriver
