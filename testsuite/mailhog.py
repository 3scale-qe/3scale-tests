"""
This module contains wrapper for the Mailhog API
"""

from datetime import datetime, timedelta, timezone
import json

import pytest
import requests
from openshift import OpenShiftPythonException
from testsuite.utils import warn_and_skip
from testsuite.openshift.client import OpenShiftClient  # pylint: disable=unused-import


def _age_gt(msg, age):
    """Compare whether message is older than given timedelta"""
    fmt = "%a, %d %b %Y %H:%M:%S %z"
    return datetime.now(timezone.utc) - datetime.strptime(msg["Content"]["Headers"]["Date"][0], fmt) > age


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
            if len(mailhog_routes) == 0:
                pytest.skip("Mailhog is misconfigured or missing")
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
        assert response.status_code == 200, f"The request to mailhog failed: {response.status_code} {response.text}"
        return response

    def _all_messages(self, start):
        """Do the paging, return all"""
        response = self.messages(start=start, limit=500)
        count = response["count"] + start
        while count < response["total"] - start:
            chunk = self.messages(start=count, limit=500)
            response["items"] += chunk["items"]
            response["count"] += chunk["count"]
            count = response["count"]
        return response

    def messages(self, start: int = 0, limit: int = 25):
        """Gets sent emails to the mailhog"""
        if limit == -1:
            return self._all_messages(start)
        params = {"start": start, "limit": limit}
        response = self.request(params=params, endpoint="api/v2/messages")
        # The quotes are in the returned json escaped by two backslashes and python
        # can not parse it, this replacements fixes it
        return json.loads(
            response.content.decode('utf8').replace('\\\\"', '\\"'))

    def __iter__(self):
        """Iterator handles paging gracefully.

        It doesn't fetch all the messages, does it in chunks.
        Safes memory and time, fetches just as much as necessary.
        """
        def generator():
            offset = 0
            total = 1
            while offset < total:
                messages = self.messages(offset, 100)
                offset += messages["count"]
                total = messages["total"]
                for i in messages["items"]:
                    yield i

        return iter(generator())

    def select(self, key, count=-1, stop=None):
        """Generator to select messages based on key function

        key takes one argument, current message and should return True o
        False. If True message is selected to the collection and yielded back.

        Args:
            :param key: a function key(message) -> bool: if True included in return
            :param count: Stop after count matches
            :param stop: a function stop(message) -> bool: if True then stop iteration
        """

        match_count = 0
        for i in iter(self):
            if 0 <= count <= match_count:
                return
            if stop and stop(i):
                return
            if key(i):
                match_count += 1
                yield i

    def find_by_subject(self, subject, count=-1, max_age=timedelta(hours=1)):
        """Return messages of given subject

        Search is limited to messages of max age 1 hour by default
        """
        stop = None if max_age is None else lambda m: _age_gt(m, max_age)
        return list(self.select(lambda m: subject == m["Content"]["Headers"]["Subject"], count, stop))

    def find_by_content(self, content, count=-1, max_age=timedelta(hours=1)):
        """Return messages that contain given content.

        Search is limited to messages of max age 1 hour by default
        """
        stop = None if max_age is None else lambda m: _age_gt(m, max_age)
        return list(self.select(lambda m: content in m["Content"]["Headers"]["Body"], count, stop))

    def delete(self, mail_id=None):
        """Deletes emails from the mailhog. If id is None all emails are deleted"""
        if mail_id is None:
            self.request(method="DELETE", endpoint="api/v1/messages")
        elif isinstance(mail_id, str):
            self.request(method="DELETE", endpoint=f"api/v1/messages/{mail_id}")
        else:
            for mail in mail_id:
                self.request(method="DELETE", endpoint=f"api/v1/messages/{mail}")
