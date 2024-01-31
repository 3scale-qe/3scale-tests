"""
Test that any char from the utf-8 encoding won't be changed by the apicast

This test is testing only subset of utf-8 chars that have different encoding than windows-1252
https://www.w3schools.com/tags/ref_urlencode.ASP
"""

from urllib.parse import urlparse, quote

import pytest

from testsuite.echoed_request import EchoedRequest

SPECIAL_CHARS = (
    "`‚ƒ„…†‡ˆ‰Š‹Œ\x8dŽ\x8f\x90‘’“”•–—˜™š›œ\x9džŸ ¡¢£¤¥¦§¨©ª«¬\xad®¯°±²³´µ¶·¸¹º»¼½¾¿"
    "ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞßàáâãäåæçèéêëìíîïðñòóôõö÷øùúûüýþÿ"
)


@pytest.fixture(scope="module")
def utf_8_special_chars():
    """Chars that have different encoding than windows-1252"""
    chars = [quote(char, encoding="utf-8") for char in SPECIAL_CHARS]

    # speed up of the test, we will create one long path with 10 chars joined together
    return ["".join(chars[i : i + 10]) for i in range(0, len(chars), 10)]


@pytest.mark.sandbag  # requires go-httpbin
def test_apicast_wont_change_path(api_client, utf_8_special_chars, backend_path):
    """Test checks if any characters from the arrays is not changed by the apicast"""
    client = api_client()
    for chars in utf_8_special_chars:
        path = f"anything/foo{chars}bar"

        response = client.get(backend_path + path)
        assert response.status_code == 200

        echoed_request = EchoedRequest.create(response)
        echoed_path = urlparse(echoed_request.json["url"]).path

        assert echoed_path == f"/{path}", f"Path doesn't match, char: {chars}"
