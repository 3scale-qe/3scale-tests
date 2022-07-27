"""
When routing policy is used together with the jwt claim check, the jwt should still
restrict the access to the resource.
"""
import pytest

from testsuite import rawobj

pytestmark = [
    pytest.mark.require_version("2.11"),
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-6410")]

ERROR_MESSAGE = "Invalid JWT check"


def add_policy(application):
    """Adds policy to the service"""
    config = rawobj.PolicyConfig("jwt_claim_check", {
        "rules": [
            {
                "methods": ['GET'],
                "operations": [{
                    "op": "==",
                    "jwt_claim": "azp",
                    "value": application['client_id'],
                    "value_type": "plain",
                    "jwt_claim_type": "plain",
                }],
                "combine_op": "and",
                "resource": "/anything/protected",
                "resource_type": "plain",
            }
        ],
        "error_message": ERROR_MESSAGE,
    })
    application.service.proxy.list().policies.append(config)


@pytest.fixture(scope="module")
def application(application):
    """Add JWT claim check policy"""
    add_policy(application)
    return application


@pytest.fixture(scope="module")
def backends_mapping(custom_backend, private_base_url):
    """
    Create backend with a "/foo" path
    """
    return {"/foo": custom_backend("foo", endpoint=private_base_url("httpbin"))}


def test_application_matching_jwt_operation(api_client, application, application_doesnt_match, rhsso_service_info):
    """
    Send a request to the endpoint '/foo/anything/protected' that is protected by the JWT claim chack policy after the
    removal of the '/foo' part routing to the backend ('/anything/protected')
    Assert that request with correct access token is authorized.
    Assert that request with invalid access token is not authorized.
    """
    client_match = api_client(application)
    token = rhsso_service_info.access_token(application)
    response = client_match.get('/foo/anything/protected/1', params={'access_token': token})
    assert response.status_code == 200

    client_doesnt_match = api_client(application_doesnt_match)
    token_doesnt_match = rhsso_service_info.access_token(application_doesnt_match)
    response = client_doesnt_match.get('/foo/anything/protected/1', params={'access_token': token_doesnt_match})

    assert response.status_code == 403
