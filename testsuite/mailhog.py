"""
This module contains wrapper for the Mailhog API
"""

from typing import Set, Optional
import backoff
import pytest
import requests

from openshift_client import OpenShiftPythonException

from testsuite.utils import warn_and_skip
from testsuite.openshift.client import OpenShiftClient


class MailhogClient:
    """Wrapper for the mailhog API"""

    def __init__(
        self, openshift: OpenShiftClient, mailhog_service_name: str = "mailhog", fallback: Optional[str] = None
    ):
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
            self._url = f"http://{mailhog_routes[0]['spec']['host']}"
        except OpenShiftPythonException:
            if fallback:
                self._url = fallback
            else:
                warn_and_skip("Can't find mailhog, skipping mailhog related tests")

        self._searched_messages_ids: Set[str] = set()
        self._session = requests.Session()

    @property
    def url(self) -> str:
        """Url of the mailhog app"""
        return self._url

    def request(self, method: str = "GET", params: dict = None, endpoint: str = None):
        """Requests the mailhog API"""
        params = params or {}

        full_url = f"{self._url}/{endpoint}"
        response = self._session.request(method=method, url=full_url, params=params)
        assert response.status_code == 200, f"The request to mailhog failed: {response.status_code} {response.text}"
        return response

    def append_to_searched_messages(self, message):
        """Append message ID to list for cleanup
        @param message: message to be cleaned
        """
        self._searched_messages_ids.add(message["ID"])

    def all_messages(self):
        """Return all messages
        @warning Can be memory exhausting use get messages_by_chunk instead"""
        all_messages = []
        for messages in self.get_messages_by_chunk():
            all_messages.extend(messages)
        return all_messages

    def get_messages_by_chunk(self, chunk_size: int = 250, limit: Optional[int] = None):
        """
        A generator function that retrieves all MailHog messages in chunks.
        @param chunk_size: The number of messages to retrieve in each chunk (default 100).
        @param limit: limits number of returned messages
        :yield: A list of MailHog messages.
        """
        # Retrieve the total number of messages
        response = self.request(endpoint="/api/v2/messages?count=0")
        total_messages = limit or int(response.json()["total"])

        # Retrieve messages in chunks
        for i in range(0, total_messages, chunk_size):
            params = {"start": i, "limit": chunk_size}
            response = self.request(params=params, endpoint="api/v2/messages")
            messages = response.json()["items"]
            yield messages

    # pylint: disable=too-many-arguments, too-many-boolean-expressions
    def find_message(self, subject=None, content=None, sender=None, receiver=None):
        """Searches for messages by content, subject, sender, receiver
        CHeck presence of all provided values"""
        matching_messages = []
        for messages in self.get_messages_by_chunk():
            for message in messages:
                if (
                    (content is not None and content not in message["Content"]["Body"])
                    or (subject is not None and subject not in message["Content"]["Headers"]["Subject"])
                    or (sender is not None and sender not in message["Content"]["Headers"]["From"])
                    or (receiver is not None and receiver not in message["Content"]["Headers"]["To"])
                ):
                    continue
                matching_messages.append(message)
                self.append_to_searched_messages(message)
        return {"count": len(matching_messages), "items": matching_messages}

    def delete(self, mail_id=None):
        """Deletes emails from the mailhog. If id is None all emails are deleted"""
        if mail_id is None:
            self.request(method="DELETE", endpoint="api/v1/messages")
        elif isinstance(mail_id, str):
            self.request(method="DELETE", endpoint=f"api/v1/messages/{mail_id}")
        else:
            for mail in mail_id:
                self.request(method="DELETE", endpoint=f"api/v1/messages/{mail}")

    def delete_searched_messages(self):
        """Deletes all searched messages"""
        if len(self._searched_messages_ids) > 0:
            self.delete(mail_id=self._searched_messages_ids)
            # Clear the list of searched message IDs
            self._searched_messages_ids.clear()

    @backoff.on_exception(backoff.fibo, AssertionError, max_tries=10, jitter=None)
    def assert_message_received(self, expected_count=1, subject=None, content=None, sender=None, receiver=None):
        """Resilient test on presence of expected message with retry,
        by provided attributes
        @param receiver: "To" part of message - receiver email of message
        @param sender: "From" part of message - sender email address
        @param subject: subject of message to search for
        @param content: content of message to search for
        @param expected_count: number of expected messages
        """
        messages = self.find_message(subject, content, sender, receiver)
        assert messages["count"] == expected_count, f"Expected {expected_count} mail, found {messages['count']}"
        return messages
