"""Selenium factory for creating  Threescale browser instances to run UI tests. """

from selenium import webdriver
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

    def __init__(self, provider, driver, ssl_verify):
        """
        Initializes factory with either specified or fetched from settings values.
        :param str optional provider: Browser provider name. One of  ('local', 'remote')
        :param str optional driver: Browser name. One of ('chrome', 'firefox')
        """
        self.provider = provider
        self.driver = driver
        self.ssl_verify = ssl_verify
        self._webdriver = None
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
                ('Certificate Error' in self._webdriver.title or
                 'Login' not in self._webdriver.title)):
            self._webdriver.get(
                "javascript:document.getElementById('invalidcert_continue')"
                ".click()"
            )

        self._webdriver.maximize_window()

    def finalize(self):
        """
        Finalize handling of webdriver.
        :raises: WebDriverError: If problem with browser happens finalization occurs.
        """
        if self.provider == 'local' or self.provider == 'remote':
            self._webdriver.quit()
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
                self._webdriver = webdriver.Chrome(executable_path=ChromeDriverManager().install())
            else:
                options = webdriver.ChromeOptions()
                options.add_argument('ignore-certificate-errors')
                self._webdriver = webdriver.Chrome(executable_path=ChromeDriverManager().install(),
                                                   chrome_options=options)
        elif self.driver == 'firefox':
            if self.ssl_verify:
                self._webdriver = webdriver.Firefox(executable_path=GeckoDriverManager().install())
            else:
                browser_profile = webdriver.FirefoxProfile()
                browser_profile.accept_untrusted_certs = True
                self._webdriver = webdriver.Firefox(firefox_profile=browser_profile,
                                                    executable_path=GeckoDriverManager().install())
        if self._webdriver is None:
            raise ValueError(
                '"{}" webdriver is not supported. Please use one of {}'
                .format(self.driver, ('chrome', 'firefox', 'edge'))
            )
        self.webdriver = self._webdriver
        return self._webdriver

    def _get_remote_driver(self):
        """
        TODO: Add support for remote webdriver
        :return:  Returns remote webdriver instance of selected browser
        :note: Should not be called directly, use :meth:get_browser to choose which browser will be used
        """
