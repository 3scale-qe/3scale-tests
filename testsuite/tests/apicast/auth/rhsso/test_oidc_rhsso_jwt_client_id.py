"""
Rewrite of the spec/functional_specs/auth/rhsso/oidc_rhsso_jwt_client_id_spec.rb
and spec/functional_specs/auth/rhsso/oidc_rhsso_jwt_client_id_reject_spec.rb
this two specs ware merged in to one parametrized test
"""

import pytest

from threescale_api.resources import Service


@pytest.fixture(params=["authorization", "query", "headers"])
def credentials_location(request):
    """Holds parametrized information where are credentials located"""
    return request.param


@pytest.fixture(params=[("azp", 200), ("foo", 403)], ids=("valid-claim", "invalid-claim"))
def jwt_claim(request):
    """
    Holds parametrized information about client_ids and response codes they
    should return
    """
    return request.param


# an issue seems to be in pytest, rhsso_setup(autouse) isn't applied here,
# therefore explicit dependency required.
# (is it because of parametrisation or some function scoped fixtures?)
# pylint: disable=unused-argument
def test_auth_client_id(rhsso_setup, api_client, service, credentials_location, jwt_claim):
    """
    Test client access when service is configured with valid jwt
    Then request made with appropriate Basic auth made has to pass as expected
    """
    claim, status_code = jwt_claim
    service.proxy.update(params={
        "credentials_location": credentials_location,
        "jwt_claim_with_client_id_type": "liquid",
        "jwt_claim_with_client_id": "{{ %s }}" % claim})

    service.proxy.deploy()
    assert service["backend_version"] == Service.AUTH_OIDC
    response = api_client().get("/get")

    assert response.status_code == status_code
