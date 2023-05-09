"""UI tests module"""

from typing import List, Dict


class Sessions:
    """
    Dict-like object that holds sessions for user accounts that were logged in
    In a form:
        (username, password, url) : cookie_dict
    """

    def __init__(self):
        super().__init__()
        self.sessions = {}

    def restore(self, browser, username, password, url):
        """
        Tries to restore session for the user.
        :param browser: the browser to which we will resume the session
        :param username: user name used in key for sessions dict
        :param password: user password used in key for sessions dict
        :param url: url used in key for sessions dict
        :return: True, if the session was restored
        """
        key = (username, password, url)
        browser.selenium.delete_all_cookies()
        if key in self.sessions:
            for cookie in self.sessions[key]:
                browser.selenium.add_cookie(cookie)
            browser.refresh()
            return True

        return False

    def save(self, username, password, url, values: List[Dict]):
        """
        Saves cookies to sessions dict under the key: (user, password, url)
        :param username: user name used in key for sessions dict
        :param password: user password used in key for sessions dict
        :param url: url used in key for sessions dict
        :param values: cookies
        """
        self.sessions[(username, password, url)] = values
