"""Selenium factory for creating  Threescale browser instances to run UI tests. """

from selenium import webdriver
from msedge.selenium_tools import EdgeOptions
from msedge.selenium_tools.remote_connection import EdgeRemoteConnection
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

    def __init__(self, provider, driver, ssl_verify, remote_url=None):
        """
        Initializes factory with either specified or fetched from settings values.
        :param str provider: Browser provider name. One of  ('local', 'remote')
        :param str driver: Browser name. One of ('chrome', 'firefox')
        :param str ssl_verify: option for certificates ignore
        :param str optional remote_url: URL of remote webdriver
        """
        self.provider = provider
        self.driver = driver
        self.ssl_verify = ssl_verify
        self.remote_url = remote_url or 'http://127.0.0.1:4444'
        self.webdriver = None

    # pylint: disable=no-else-return
    def get_driver(self):
        """
        Returns selenium webdriver instance of selected provider and browser.

        :return: selenium webdriver instance
        :raises: ValueError: If wrong provider or browser specified.
        """
        if self.provider == 'local':
            return self._get_selenium_driver()
        elif self.provider == 'remote':
            return self._get_remote_driver()
        else:
            raise ValueError(
                '"{}" browser is not supported. Please use one of {}'
                .format(self.provider, ('local', 'remote'))
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
        if self.provider == 'local' or self.provider == 'remote':
            self.webdriver.quit()
        else:
            raise WebDriverError("Problem with browser finalization")

    def _get_selenium_driver(self):
        """
        Returns selenium webdriver instance of selected browser.
        :note: Should not be called directly, use :meth:get_driver to choose which browser will be used.
        :raises: ValueError: If wrong browser is specified.
        """
        if self.driver == 'chrome':
            if self.ssl_verify:
                self.webdriver = webdriver.Chrome(executable_path=ChromeDriverManager().install())
            else:
                options = webdriver.ChromeOptions()
                options.set_capability("acceptInsecureCerts", True)
                self.webdriver = webdriver.Chrome(executable_path=ChromeDriverManager().install(),
                                                  chrome_options=options)
        elif self.driver == 'firefox':
            if self.ssl_verify:
                self.webdriver = webdriver.Firefox(executable_path=GeckoDriverManager().install())
            else:
                browser_profile = webdriver.FirefoxProfile()
                browser_profile.accept_untrusted_certs = True
                self.webdriver = webdriver.Firefox(firefox_profile=browser_profile,
                                                   executable_path=GeckoDriverManager().install())
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
            command_executor = self.remote_url + '/wd/hub'
        elif self.driver == 'firefox':
            browser_options = webdriver.FirefoxOptions()
            command_executor = self.remote_url + '/wd/hub'
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
