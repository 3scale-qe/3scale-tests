"""Represents mockserver calls used in tests"""

from urllib.parse import urljoin
import json

from requests import HTTPError
from weakget import weakget
import backoff
import requests

from testsuite.utils import generate_tail


class Mockserver:
    """mockserver interface

    Also implements RequestBinClient interface to replace requestbin. Therefore
    `url` attribute returns URL suitable for webhooks instead of own URL. `url`
    is randomized per instance to a) make matching bit easier, b) allow
    bit of concurrency.
    """

    def __init__(self, url, verify=True):
        self._url = url
        self.verify = verify
        self._webhook = f"/webhook/{generate_tail()}"
        self.url = urljoin(self._url, self._webhook)

    def temporary_fail_request(self, num, status=500):
        """Create failing call for num occurences"""
        response = requests.put(
            urljoin(self._url, "/mockserver/expectation"),
            verify=self.verify,
            data=json.dumps(
                {
                    "httpRequest": {"path": f"/fail-request/{num}/{status}"},
                    "times": {"remainingTimes": num, "unlimited": False},
                    "httpResponse": {"statusCode": status},
                }
            ),
        )
        response.raise_for_status()
        return response

    @backoff.on_predicate(backoff.fibo, lambda x: x is None, max_tries=5, jitter=None)
    def get_webhook(self, action: str, entity_id: str):
        """
        Reimplementation of interface from RequestBinClient
        :return webhook for given action and entity_id
        """
        try:
            matcher = {
                "method": "POST",
                "path": self._webhook,
                "body": {
                    "type": "XPATH",
                    # this is xpath, it's long
                    # pylint: disable=line-too-long
                    "xpath": f'/event[action/text() = "{action}"]/object/*[local-name() = /event/type/text()]/id[text() = "{entity_id}"]',  # noqa
                },
            }
            response = self._retrieve(matcher)
        except requests.exceptions.HTTPError:
            return None
        return weakget(response.json())[-1]["httpRequest"]["body"]["xml"] % None

    def _retrieve(self, matcher):
        """Do mockserver/retrieve"""
        response = requests.put(
            urljoin(self._url, "/mockserver/retrieve"),
            params={"type": "REQUEST_RESPONSES"},
            data=json.dumps(matcher),
            verify=self.verify,
        )
        response.raise_for_status()
        return response

    def verify_sequence(self, expected_requests) -> bool:
        """Verifies that a sequence of requests was received on a Mockserver"""
        response = requests.put(
            urljoin(self._url, "/mockserver/verifySequence"),
            data=json.dumps({"httpRequests": expected_requests}),
            verify=self.verify,
        )
        if response.status_code == 400:
            raise HTTPError("Invalid matcher format", response=response)
        return response.status_code == 202
