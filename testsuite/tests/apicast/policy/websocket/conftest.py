"""Conftest for websocket policy tests"""
import contextlib
import ssl
from urllib.parse import urljoin

import backoff
import pytest
from websocket import WebSocketBadStatusException, create_connection

from testsuite import rawobj


@pytest.fixture(scope="module")
def policy_settings():
    """config for websocket policy"""
    return rawobj.PolicyConfig("websocket", {})


@pytest.fixture(scope="module")
def service_proxy_settings(private_base_url):
    """Websocket are only available on httpbin go"""
    return rawobj.Proxy(private_base_url("httpbin_go"))


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


@contextlib.contextmanager
def wsconnect(uri, options):
    """context manager for websocket"""
    websocket = create_connection(uri, **options)
    yield websocket
    websocket.close()


@backoff.on_exception(backoff.fibo, WebSocketBadStatusException, max_tries=8, jitter=None)
def retry_sucessful(websocket_uri, message, websocket_options):
    """
    Retry for websocket when we expect successful message delivery.
    :param websocket_uri: websocket uri
    :param message: message
    :param websocket_options: websocket options
    :return: received message
    """
    with wsconnect(websocket_uri, websocket_options) as websocket:
        websocket.send(message)
        return websocket.recv()


@backoff.on_predicate(backoff.fibo, lambda x: not x, max_tries=8, jitter=None)
def retry_failing(websocket_uri, expected_message, websocket_options):
    """
    Retry for websockets when we expect specific exception message.
    :param websocket_uri: websocket uri
    :param expected_message expected exception message
    :param websocket_options: websocket options
    :return: caught exception message
    """
    try:
        with wsconnect(websocket_uri, websocket_options):
            return "Connection successful"
    except WebSocketBadStatusException as exception:
        return exception.args[0] if expected_message in exception.args[0] else ""
