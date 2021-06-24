"""UI tests module"""

from typing import List, Dict, NamedTuple


class Sessions:
    """
    Dict-like object that holds sessions for user accounts that were logged in
    In a form:
        (username, password, url) : cookie_dict
    """
    def __init__(self, browser):
        super().__init__()
        self.browser = browser
        self.sessions = {}

    def restore(self, username, password, url):
        """
        Tries to restore session for the user.
        :param username: user name used in key for sessions dict
        :param password: user password used in key for sessions dict
        :param url: url used in key for sessions dict
        :return: True, if the session was restored
        """
        key = (username, password, url)
        self.browser.selenium.delete_all_cookies()
        if key in self.sessions:
            for cookie in self.sessions[key]:
                self.browser.selenium.add_cookie(cookie)
            self.browser.refresh()
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


class BillingAddress(NamedTuple):
    """Billing address"""
    name: str
    address: str
    city: str
    country: str
    state: str
    phone: str
    zip: str


class CreditCard(NamedTuple):
    """Credit card"""
    number: str
    cvc: str
    exp_month: int
    exp_year: int

    # def stripe(self):
    #     obj = {
    #         "name": self.name,
    #         "address1": self.address,
    #         "city": self.city,
    #         "country": self.country,
    #         "state": self.state,
    #         "phone": self.phone,
    #         "postal": self.zip,
    #     }
    #
    #     return obj
