"""
Rewrite spec/functional_specs/api_default_spec.rb
"""
import pytest
from testsuite.gateways.gateways import Capability


def test_staging(api_client):
    """
    Test request has to pass and return HTTP 200 for staging client.
    """
    response = api_client().get('/get')
    assert response.status_code == 200


@pytest.mark.disruptive
@pytest.mark.required_capabilities(Capability.PRODUCTION_GATEWAY)
def test_production(prod_client):
    """
    Test request has to pass and return HTTP 200 for prod. client.
    """
    response = prod_client().get('/get')
    assert response.status_code == 200
