"testsuite helpers"

import getpass
import secrets
import time
import typing

import requests

from hyper.contrib import HTTP20Adapter
from requests.packages.urllib3.util.retry import Retry  # noqa # pylint: disable=import-error

if typing.TYPE_CHECKING:
    from _pytest.fixtures import FixtureRequest


def randomize(name):
    "To avoid conflicts returns modified name with random sufffix"
    return "%s-%s" % (name, secrets.token_urlsafe(5).translate(str.maketrans("", "", "-_")).lower())


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


def blame(request: 'FixtureRequest', name: str, tail: int = 3) -> str:
    """Create 'scoped' name within given test

    This returns unique name for 3scale object(s) to avoid conflicts

    Args:
        :param request: current pytest request
        :param name: Base name, e.g. 'svc'
        :param tail: length of random suffix"""

    nodename = request.node.name
    if nodename.startswith("test_"):  # is this always true?
        nodename = nodename[5:]

    whoami = getpass.getuser()
    context = nodename.lower().split("_")[0]
    if len(context) > 2:
        context = context[:2] + context[2:-1].translate(str.maketrans("", "", "aiyu")) + context[-1]
    suffix = secrets.token_urlsafe(tail).lower()

    return f"{name[:8]}-{whoami[:8]}-{context[:9]}-{suffix}"


def blame_desc(request: 'FixtureRequest', text: str = None):
    """Returns string of text with details about execution suitable as description for 3scale objects"""

    nodename = request.node.name
    whoami = getpass.getuser()
    now = time.asctime()

    # make it more unique
    tail = secrets.token_urlsafe(3).lower()

    desc = f"Created for '{nodename}' executed by '{whoami}' at {now} ({tail})"
    if text not in (None, ""):
        desc = f"{text}\n\n{desc}"

    return desc
