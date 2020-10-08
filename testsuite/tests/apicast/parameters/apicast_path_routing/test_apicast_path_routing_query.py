"""
Test that path based routing does match args
"""
import pytest
import requests

from packaging.version import Version  # noqa # pylint: disable=unused-import
from testsuite import TESTED_VERSION, rawobj  # noqa # pylint: disable=unused-import
from testsuite.echoed_request import EchoedRequest
from testsuite.gateways.gateways import Capability

pytestmark = [pytest.mark.required_capabilities(Capability.STANDARD_GATEWAY),
              pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-5149"),
              pytest.mark.skipif("TESTED_VERSION < Version('2.9')")]


@pytest.fixture(scope="module")
def gateway_environment(gateway_environment):
    """Enables path routing on gateway"""
    gateway_environment.update({"APICAST_PATH_ROUTING": 1})
    return gateway_environment


@pytest.fixture(scope="module")
def service2_proxy_settings(private_base_url):
    """Websocket are only available on httpbin"""
    return rawobj.Proxy(private_base_url("httpbin"))


@pytest.fixture(scope="module")
def service2(service2):
    """
    Add the mapping rule with pattern that contains query param /anything/foo?baz={baz}
    """
    proxy = service2.proxy.list()

    metric = service2.metrics.list()[0]
    proxy.mapping_rules.create(rawobj.Mapping(metric, pattern="/anything/foo?baz={baz}", http_method='GET'))
    proxy.update()

    return service2


def test_args(api_client2):
    """
    Checks that request with query param will match mapping rule
    """
    response = api_client2.get('/anything/foo', params=dict(baz='baz'))

    assert response.status_code == 200

    echoed_request = EchoedRequest.create(response)
    assert echoed_request.params.get('baz') == 'baz'


def test_args_another_service(api_client):
    """
    Checks that request with matching mapping rule of another service will fail

    NOTE: needs to be here to create first service in order to test path based routing
    """
    response = api_client.get('/anything/foo', params={'baz': 'baz'})

    assert response.status_code == 403


def test_non_matching_args(application2):
    """
    Checks that request with correct path from mapping rule and:
                    - with wrong query param will fail
                    - without query param will fail
    """
    session = requests.Session()
    session.auth = application2.authobj

    client = application2.api_client(session=session)
    assert client.get('/anything/foo', params={'bar': 'baz'}).status_code == 404
    assert client.get('/anything/foo').status_code == 404
