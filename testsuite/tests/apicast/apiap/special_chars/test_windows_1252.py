"""
Test that any char from the windows-1252 encoding won't be changed by the apicast
"""
from urllib.parse import urlparse

import pytest

from packaging.version import Version  # noqa # pylint: disable=unused-import
from testsuite.echoed_request import EchoedRequest
from testsuite import TESTED_VERSION  # noqa # pylint: disable=unused-import

pytestmark = [
    pytest.mark.skipif("TESTED_VERSION < Version('2.11')"),
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-6834")]

HEX_CHARS = "0123456789ABCDEF"


@pytest.fixture()
def windows_1252_chars():
    """
    Generate all chars from windows-1252 encoding

    We need to exclude a-z, A-Z, 0-9, -, ., _, ~ chars since they should be decoded
    https://tools.ietf.org/html/rfc3986#section-2.3
    Also we need to exclude NUL (%00)
    """
    chars = set(f"%{char1}{char2}" for char1 in HEX_CHARS for char2 in HEX_CHARS)

    # remove 0-9 chars
    chars -= set(f"%3{i}" for i in range(10))
    # remove A-O
    chars -= set(f"%4{char}" for char in HEX_CHARS[1:])
    # remove P-Z
    chars -= set(f"%5{char}" for char in HEX_CHARS[:11])
    # remove a-o
    chars -= set(f"%6{char}" for char in HEX_CHARS[1:])
    # remove p-z
    chars -= set(f"%7{char}" for char in HEX_CHARS[:11])
    # remove - . _ ~
    chars -= {"%2D", "%2E", "%5F", "%7E"}
    # remove NUL
    chars -= {"%00"}

    chars = list(chars)

    # speed up of the test, we will create one long path with 10 chars joined together
    return [''.join(chars[i:i + 10]) for i in range(0, len(chars), 10)]


def test_apicast_wont_change_path(api_client, windows_1252_chars, backend_path):
    """Test checks if any character from the windows 1252 chars is not changed by the apicast"""
    client = api_client(disable_retry_status_list={404, 503})
    for char in windows_1252_chars:
        path = f"anything/foo{char}bar"

        response = client.get(backend_path + path)
        assert response.status_code == 200, f"Path: {path}"

        echoed_request = EchoedRequest.create(response)
        echoed_path = urlparse(echoed_request.json["url"]).path

        assert echoed_path == f"/{path}", f"Path doesn't match, char: {char}"
