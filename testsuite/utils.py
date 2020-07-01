"testsuite helpers"

import datetime
import getpass
import secrets
import time
import typing
from base64 import b64encode
from os import urandom

import requests

from hyper.contrib import HTTP20Adapter
from requests.packages.urllib3.util.retry import Retry  # noqa # pylint: disable=import-error

if typing.TYPE_CHECKING:
    from _pytest.fixtures import FixtureRequest


def randomize(name, tail=5):
    "To avoid conflicts returns modified name with random sufffix"
    return "%s-%s" % (name, secrets.token_urlsafe(tail).translate(str.maketrans("", "", "-_")).lower())


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

    return randomize(f"{name[:8]}-{whoami[:8]}-{context[:9]}", tail=tail)


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


def random_string(num_bytes):
    """Generates random string for given number of bytes"""
    random_bytes = urandom(num_bytes)
    return b64encode(random_bytes).decode('utf-8')


def wait_interval(min_sec=15, max_sec=45):
    """
    The requests has to be send between the 15th and 45th second of the minute
    When the time is outside of this interval, waits until the start of a next one
    """
    seconds = datetime.datetime.now().second
    if seconds < min_sec or seconds > max_sec:
        sleep_time = (60 - seconds + min_sec) % 60
        time.sleep(sleep_time)


def wait_until_next_minute(min_sec=15, max_sec=45):
    """
     Waits until the start of the next minute when are the limits reseted,
     then waits until the start of the interval allowed to sent requests
    """
    seconds = datetime.datetime.now().second
    time.sleep(60 - seconds)
    if min_sec < seconds < max_sec:
        wait_interval()


def wait_interval_hour(max_min, min_min=0):
    """
    Prevents sending the request in the beginning or at the end of an hour
    Prevents refreshing the limits during the test
    """
    minutes = datetime.datetime.now().minute
    if minutes < min_min or minutes > max_min:
        sleep_time = ((60 - minutes + min_min) % 60) * 60 + 10
        time.sleep(sleep_time)
