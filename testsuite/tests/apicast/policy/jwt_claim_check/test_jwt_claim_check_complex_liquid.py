"""
Regression test for https://issues.redhat.com/browse/THREESCALE-3968
"""
import pytest

from testsuite import rawobj
from testsuite.rhsso.rhsso import OIDCClientAuth
from testsuite.utils import randomize

ERROR_MESSAGE = "Invalid JWT check"


def add_policy(application):
    """Adds policy to the service"""
    config = rawobj.PolicyConfig("jwt_claim_check", {
        "rules": [
            {
                "methods": ['GET'],
                "operations": [{
                    "op": "==",
                    "jwt_claim": f"{{{{ azp | replace: '{application['client_id']}', 'foo'}}}}",
                    "value": "foo",
                    "value_type": "plain",
                    "jwt_claim_type": "liquid",
                }],
                "combine_op": "and",
                "resource": "/get",
                "resource_type": "plain",
            }
        ],
        "error_message": ERROR_MESSAGE,
    })
    application.service.proxy.list().policies.append(config)


@pytest.fixture(scope="module")
def application(rhsso_service_info, application):
    """Add OIDC client authentication"""
    application.register_auth("oidc", OIDCClientAuth(rhsso_service_info))
    add_policy(application)
    return application


@pytest.fixture(scope="module")
def application_doesnt_match(service, custom_application, custom_app_plan, rhsso_service_info):
    """Second application that doesn't match jwt claim check policy"""
    plan = custom_app_plan(rawobj.ApplicationPlan(randomize("AppPlan")), service)
    application = custom_application(rawobj.Application(randomize("App"), plan))
    application.register_auth("oidc", OIDCClientAuth(rhsso_service_info))
    return application


def test_application_matching_jwt_operation(api_client, application, application_doesnt_match, rhsso_service_info):
    """
    Test application that match policy will succeed with the request
         application that doesn't match policy will be rejected with correct message
    """
    app_key = application.keys.list()["keys"][0]["key"]["value"]
    token = rhsso_service_info.password_authorize(application["client_id"], app_key).token['access_token']
    assert api_client.get('/get', params={'access_token': token}).status_code == 200

    app_key = application_doesnt_match.keys.list()["keys"][0]["key"]["value"]
    token = rhsso_service_info.password_authorize(application_doesnt_match["client_id"], app_key).token['access_token']
    response = application_doesnt_match.api_client().get('/get', params={'access_token': token})

    assert response.status_code == 403
    assert response.text == ERROR_MESSAGE + "\n"
