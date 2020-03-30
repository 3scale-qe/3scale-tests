"testsuite helpers"
import secrets

import requests

from hyper.contrib import HTTP20Adapter
from requests.packages.urllib3.util.retry import Retry  # noqa # pylint: disable=import-error


def randomize(name):
    "To avoid conflicts returns modified name with random sufffix"
    return "%s-%s" % (name, secrets.token_urlsafe(8).lower())


def retry_for_session(session: requests.Session, total: int = 8):
    """Adds retry for requests session with HTTP/2 adapter"""
    retry = Retry(
        total=total,
        backoff_factor=1,
        status_forcelist=(503, 404),
    )
    adapter = HTTP20Adapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
