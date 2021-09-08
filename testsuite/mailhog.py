"""
This module contains wrapper for the Mailhog API
"""

import json
import requests
from openshift import OpenShiftPythonException
from testsuite.utils import warn_and_skip
from testsuite.openshift.client import OpenShiftClient  # pylint: disable=unused-import


class MailhogClient:
    """Wrapper for the mailhog API"""

    def __init__(self, openshift: 'OpenShiftClient',
                 mailhog_service_name: str = "mailhog", fallback=None):
        """Initializes the client, the mailhog app has to be running in the
            same openshift as 3scale, and has to be named 'mailhog'"""
        # mailhog is first searched in 3scale namespace, if that fails
        # tools is second choice, this is intentional order, tests assume
        # exclusive mailhog instance, therefore a 'private' instance is always
        # first choice
        try:
            mailhog_routes = openshift.routes.for_service(mailhog_service_name)
            assert len(mailhog_routes) > 0, "Mailhog is misconfigured or missing"
            self._url = \
                "http://" + mailhog_routes[0]["spec"]["host"]
        except OpenShiftPythonException:
            if fallback:
                self._url = fallback
            else:
                warn_and_skip("Can't find mailhog, skipping mailhog related tests")

    @property
    def url(self) -> str:
        """Url of the mailhog app"""
        return self._url

    def request(self, method: str = "GET", params=None, endpoint: str = None):
        """Requests the mailhog API"""
        params = params or {}

        full_url = self._url + "/" + endpoint
        response = requests.request(method=method, url=full_url,
                                    params=params, verify=False)
        assert response.status_code == 200, 'The request to mailhog failed'
        return response

    def messages(self, start: int = 0, limit: int = 25):
        """Gets sent emails to the mailhog"""
        params = {"start": start, "limit": limit}
        response = self.request(params=params, endpoint="/api/v2/messages")
        # The quotes are in the returned json escaped by two backslashes and python
        # can not parse it, this replacements fixes it
        return json.loads(
            response.content.decode('utf8').replace('\\\\"', '\\"'))

    def delete(self):
        """Deletes all emails from the mailhog"""
        self.request(method="DELETE", endpoint="/api/v1/messages")
