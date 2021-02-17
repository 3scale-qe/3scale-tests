"""
Rewrite: ./spec/functional_specs/api_update_url_spec.rb
"""

import pytest
from testsuite.utils import blame
from testsuite.gateways.gateways import Capability


pytestmark = pytest.mark.issue("https://issues.jboss.org/browse/THREESCALE-2939")


@pytest.fixture(scope="module")
def proxy_update(service, configuration, request):
    """
     Updates endpoint and sandbox endpoint.
    :returns updated params
    """
    prefix = blame(request, "svc")
    superdomain = configuration.superdomain
    params = {
        "endpoint": f"https://{prefix}-2-production.{superdomain}:443",
        "sandbox_endpoint": f"https://{prefix}-2-staging.{superdomain}:443"
    }

    service.proxy.list().update(params)
    service.proxy.deploy()

    return params


def test_api_client(api_client):
    """
    Test request has to pass and return HTTP 200 for staging client
    """
    response = api_client().get('/get')
    assert response.status_code == 200


@pytest.mark.disruptive
@pytest.mark.required_capabilities(Capability.PRODUCTION_GATEWAY)
def test_prod_client(prod_client):
    """
    Test request has to pass and return HTTP 200 for prod. client.
    """
    response = prod_client().get('/get')
    assert response.status_code == 200


def test_proxy_update(service, proxy_update):
    """
    Tests checks if the updated endpoints match.
    """
    proxy = service.proxy.list()
    assert proxy['endpoint'] == proxy_update['endpoint']
    assert proxy['sandbox_endpoint'] == proxy_update['sandbox_endpoint']
