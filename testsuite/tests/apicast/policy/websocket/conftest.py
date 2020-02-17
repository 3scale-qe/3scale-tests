"""Conftest for websocket policy tests"""
import ssl
from urllib.parse import urljoin

import pytest

from testsuite import rawobj


@pytest.fixture(scope="module")
def policy_settings():
    """config for websocket policy"""
    return rawobj.PolicyConfig("websocket", {})


@pytest.fixture(scope="module")
def service_proxy_settings(private_base_url):
    """Websocket are only available on httpbin go"""
    return rawobj.Proxy(private_base_url("httpbin-go"))


@pytest.fixture
def websocket_uri(application):
    """Websocket URI in format: wss://<apicast-url>/websocket-echo"""
    url = application.service.proxy.list()['sandbox_endpoint']\
        .replace("https://", "wss://", 1)\
        .replace("http://", "ws://", 1)

    url = urljoin(url, "/websocket-echo")
    return url


@pytest.fixture
def websocket_options(testconfig):
    """Websocket options"""
    options = {"sslopt": {} if testconfig["ssl_verify"] else {"cert_reqs": ssl.CERT_NONE}}
    return options
