"""
View representations of 3scale API Docs pages
"""

import backoff
from widgetastic.widget import Text, View

from testsuite.ui.views.admin.settings import BaseSettingsView
from testsuite.ui.widgets.oas3 import Endpoint


class APIDocsView(BaseSettingsView):
    """
    View representation of API Docs page
    """

    path_pattern = "/p/admin/api_docs"
    page_title = Text(locator='//*[@id="content"]/h1')
    service_management_api_category = Text(locator='//*[@data-name="service_management_api"]')
    account_management_api_category = Text(locator='//*[@data-name="account_management_api"]')
    policy_registry_api_category = Text(locator='//*[@data-name="policy_registry_api"]')
    endpoint = View.nested(Endpoint)

    def prerequisite(self):
        return BaseSettingsView

    @backoff.on_predicate(backoff.fibo, lambda x: x < 200, max_tries=8)
    def post_navigate(self, **kwargs):
        """
        APIDocsView loads Endpoints dynamically with js script.
        Once navigated to this View, Navigator waits for all API endpoint sections to be loaded.
        """
        return len(self.endpoint)

    @property
    def is_displayed(self):
        return (
            BaseSettingsView.is_displayed.fget(self)
            and self.path in self.browser.url
            and self.page_title.is_displayed
            and self.service_management_api_category.is_displayed
            and self.account_management_api_category.is_displayed
            and self.policy_registry_api_category.is_displayed
            and self.page_title.text == "3scale API Documentation"
        )
