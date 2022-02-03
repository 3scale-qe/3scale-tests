"""
Test that http routes will be created and managed by zync
"""

from urllib.parse import urlparse

from packaging.version import Version  # noqa # pylint: disable=unused-import

import pytest

from testsuite import TESTED_VERSION  # noqa # pylint: disable=unused-import
from testsuite.capabilities import Capability

# This test can be done only with system apicast
pytestmark = [pytest.mark.skipif("TESTED_VERSION < Version('2.9')"),
              pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-3545"),
              pytest.mark.required_capabilities(Capability.SAME_CLUSTER, Capability.PRODUCTION_GATEWAY),
              pytest.mark.disruptive]


@pytest.fixture(scope='module')
def service(service):
    """Change staging and production url to http:// with port 80"""
    stage_base = urlparse(service.proxy.list()['sandbox_endpoint']).hostname
    prod_base = urlparse(service.proxy.list()['endpoint']).hostname
    service.proxy.list().update({
        "sandbox_endpoint": f"http://{stage_base}:80",
        "endpoint": f"http://{prod_base}:80"
    })
    service.proxy.deploy()
    return service


def test_successful_requests(api_client, prod_client, application, logger):
    """
    Test that apicast routes with http will be created by zync
    """
    # staging
    response = api_client().get('/get')
    assert response.status_code == 200

    logger.info("response.url: %s", response.url)
    logger.info("response.request.url: %s", response.request.url)
    request_url = urlparse(str(response.url))
    assert request_url.scheme == 'http'
    assert request_url.port == 80

    # production
    response = prod_client(application).get('/get')
    assert response.status_code == 200

    request_url = urlparse(str(response.url))
    assert request_url.scheme == 'http'
    assert request_url.port == 80
