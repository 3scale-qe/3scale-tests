"""
Rewrite spec/functional_specs/policies/jwt_claim_check/jwt_claim_check_spec.rb
"""

import pytest

from testsuite import rawobj

ERROR_MESSAGE = "Invalid JWT check"


def add_policy(application):
    """Adds policy to the service"""
    config = rawobj.PolicyConfig(
        "jwt_claim_check",
        {
            "rules": [
                {
                    "methods": ["GET"],
                    "operations": [
                        {
                            "op": "==",
                            "jwt_claim": "azp",
                            "value": application["client_id"],
                            "value_type": "plain",
                            "jwt_claim_type": "plain",
                        }
                    ],
                    "combine_op": "and",
                    "resource": "/get",
                    "resource_type": "plain",
                }
            ],
            "error_message": ERROR_MESSAGE,
        },
    )
    application.service.proxy.list().policies.append(config)


@pytest.fixture(scope="module")
def application(application):
    """Add OIDC client authentication"""
    add_policy(application)
    return application


def test_application_matching_jwt_operation(api_client, application, application_doesnt_match, rhsso_service_info):
    """
    Test application that match policy will succeed with the request
         application that doesn't match policy will be rejected with correct message
    """
    client_match = api_client()
    client_doesnt_match = api_client(application_doesnt_match)

    token = rhsso_service_info.access_token(application)
    assert client_match.get("/get", params={"access_token": token}).status_code == 200

    token = rhsso_service_info.access_token(application)
    response = client_doesnt_match.get("/get", params={"access_token": token})

    assert response.status_code == 403
    assert response.text == ERROR_MESSAGE + "\n"
