"testsuite helpers"

import os
import secrets
import time
import typing
import warnings
from base64 import b64encode
from datetime import datetime, timezone
from os import urandom
from pathlib import Path

import pytest

from testsuite.config import settings

if typing.TYPE_CHECKING:
    from _pytest.fixtures import FixtureRequest


def generate_tail(tail=5):
    """Returns random suffix"""
    return secrets.token_urlsafe(tail).translate(str.maketrans("", "", "-_")).lower()


def randomize(name, tail=5):
    "To avoid conflicts returns modified name with random sufffix"
    return "%s-%s" % (name, generate_tail(tail))


def _whoami():
    """Returns username"""
    if "tester" in settings:
        return settings["tester"]

    try:
        return os.getlogin()
    # want to catch broad exception and fallback at any circumstance
    # pylint: disable=broad-except
    except Exception:
        return str(os.getuid())


def blame(request: "FixtureRequest", name: str, tail: int = 5) -> str:
    """Create 'scoped' name within given test

    This returns unique name for 3scale object(s) to avoid conflicts

    Args:
        :param request: current pytest request
        :param name: Base name, e.g. 'svc'
        :param tail: length of random suffix"""

    nodename = request.node.name
    if nodename.startswith("test_"):  # is this always true?
        nodename = nodename[5:]

    context = nodename.lower().split("_")[0]
    if len(context) > 2:
        context = context[:2] + context[2:-1].translate(str.maketrans("", "", "aiyu")) + context[-1]

    if "." in context:
        context = context.split(".")[0]

    return randomize(f"{name[:8]}-{_whoami()[:6]}-{context[:9]}", tail=tail)


def blame_desc(request: "FixtureRequest", text: str = None):
    """Returns string of text with details about execution suitable as description for 3scale objects"""

    nodename = request.node.name
    now = time.asctime()

    # make it more unique
    tail = secrets.token_urlsafe(3).lower()

    desc = f"Created for '{nodename}' executed by '{_whoami()}' at {now} ({tail})"
    if text not in (None, ""):
        desc = f"{text}\n\n{desc}"

    return desc


def random_string(num_bytes):
    """Generates random string for given number of bytes"""
    random_bytes = urandom(num_bytes)
    return b64encode(random_bytes).decode("utf-8")[:num_bytes]


def _to_bytes(value, encoding="utf-8"):
    """Encodes string to bytes"""
    return value.encode(encoding)


def basic_auth_string(key, value):
    """Returns basic auth string from key and value"""
    key_pass = b":".join((_to_bytes(key), _to_bytes(value)))
    token = b64encode(key_pass).decode()
    return f"Basic {token}"


def wait_interval(min_sec=15, max_sec=45):
    """
    The requests has to be send between the 15th and 45th second of the minute
    When the time is outside of this interval, waits until the start of a next one
    """
    seconds = datetime.now(timezone.utc).second
    if seconds < min_sec or seconds > max_sec:
        sleep_time = (60 - seconds + min_sec) % 60
        time.sleep(sleep_time)


def wait_until_next_minute(min_sec=15, max_sec=45):
    """
    Waits until the start of the next minute when are the limits reseted,
    then waits until the start of the interval allowed to sent requests
    """
    seconds = datetime.now(timezone.utc).second
    time.sleep(60 - seconds)
    if min_sec < seconds < max_sec:
        wait_interval()


def wait_interval_hour(max_min, min_min=0):
    """
    Prevents sending the request in the beginning or at the end of an hour
    Prevents refreshing the limits during the test
    """
    minutes = datetime.now(timezone.utc).minute
    if minutes < min_min or minutes > max_min:
        sleep_time = ((60 - minutes + min_min) % 60) * 60 + 10
        time.sleep(sleep_time)


def _warn_and_skip(message, action):
    """switch/case for warn_and_skip"""
    if action != "quiet":
        warnings.warn(message)
    if action in ("warn", "quiet"):
        pytest.skip(message)
    else:
        pytest.fail(message)


def warn_and_skip(message, action="warn"):
    """
    Prints warning and skips the test
    """
    rules = settings.get("warn_and_skip", {})
    current = os.environ["PYTEST_CURRENT_TEST"]

    for key in sorted(rules.keys(), key=len, reverse=True):
        if current.startswith(key):
            _warn_and_skip(message, rules[key])
            return
    _warn_and_skip(message, action)


def custom_policy() -> dict:
    """Returns a dict containing a custom policy based on https://github.com/3scale-qe/apicast-example-policy"""
    initlua = "return require('example')"
    apicastpolicyjson = """
    {
        "$schema": "http://apicast.io/policy-v1/schema#manifest#",
        "name": "APIcast Example Policy",
        "summary": "This is just an example.",
        "description": "This policy is just an example how to write your custom policy.",
        "version": "0.1",
        "configuration": {
            "type": "object",
            "properties": { }
        }
    }
    """
    examplelua = """
    local setmetatable = setmetatable

    local _M = require('apicast.policy').new('Example', '0.1')
    local mt = { __index = _M }

    function _M.new()
    return setmetatable({}, mt)
    end

    function _M:init()
    ngx.log(ngx.DEBUG, "example policy initialized")
    -- do work when nginx master process starts
    end

    function _M:init_worker()
    -- do work when nginx worker process is forked from master
    end

    function _M:rewrite()
    -- change the request before it reaches upstream
    ngx.req.set_header('X-Example-Policy-Request', 'HERE')
    end

    function _M:access()
    -- ability to deny the request before it is sent upstream
    end

    function _M:content()
    -- can create content instead of connecting to upstream
    end

    function _M:post_action()
    -- do something after the response was sent to the client
    end

    function _M:header_filter()
    -- can change response headers
    ngx.header['X-Example-Policy-Response'] = 'TEST'
    end

    function _M:body_filter()
    -- can read and change response body
    -- https://github.com/openresty/lua-nginx-module/blob/master/README.markdown#body_filter_by_lua
    end

    function _M:log()
    -- can do extra logging
    end

    function _M:balancer()
    -- use for example require('resty.balancer.round_robin').call to do load balancing
    end

    return _M
    """
    return {"init.lua": initlua, "example.lua": examplelua, "apicast-policy.json": apicastpolicyjson}


def get_results_dir_path():
    """resolve resultsdir or defaults to root of 3scale-tests repo"""
    no_argument_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../..")
    resultsdir = os.environ.get("resultsdir", no_argument_dir)
    return Path(resultsdir)
