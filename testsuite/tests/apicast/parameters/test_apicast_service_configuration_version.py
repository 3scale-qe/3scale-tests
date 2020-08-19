"""Rewrite of spec/openshift_specs/apicast_api_version_spec.rb

Force apicast to use a specific configuration version by setting
`APICAST__SERVICE_<SERVICE ID>_CONFIGURATION_VERSION` environment variable.
"""
import pytest

import threescale_api.auth

from testsuite.gateways.gateways import Capability
from testsuite import rawobj

pytestmark = pytest.mark.required_capabilities(Capability.STANDARD_GATEWAY)


@pytest.fixture(scope="module")
def service(service, private_base_url, staging_gateway):
    """Forces apicast to work only with version 1 of this service's configuration.

    Sets service configuration version environment"""

    proxy = service.proxy.list()
    # update proxy credentials so that we can have a version 2 of it
    proxy.update(rawobj.Proxy(private_base_url(), credentials_location="authorization"))

    staging_gateway.environ[f"APICAST_SERVICE_{service.entity_id}_CONFIGURATION_VERSION"] = 1

    return service


def test_should_basic_authenticaton_returns_forbidden(api_client):
    """Call to apicast with authorization credential location should return 403."""
    assert api_client.get("/get").status_code == 403


def test_should_query_authentication_returns_ok(application):
    """Call to apicast with query credential location should return 200."""
    client = application.api_client()
    # pylint: disable=protected-access
    client._session.auth = threescale_api.auth.UserKeyAuth(application, "query")

    assert client.get("/get").status_code == 200
