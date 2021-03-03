"""
Rewrite: ./spec/functional_specs/apicast_debug_header_spec.rb
"""

import pytest


@pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-1849")
def test_make_request(api_client, service, application):
    """
    Response containing debug header should return status code 200 and contain following headers:
    - 'X-3scale-matched-rules' - Which mapping rule was matched
    - 'X-3scale-credentials' - Credentials that were used
    - if  they contain 'X-3scale-usage' and 'X-3scale-hostname'
    - 'X-3scale-service-id' - What service id was used
    - 'X-3scale-service-name' - What is the service name
    """
    user_key = application.authobj().credentials["user_key"]
    debug_header = service.proxy.list().configs.latest()['content']['backend_authentication_value']

    response = api_client().get('/get', headers={'X-3scale-Debug': debug_header})

    assert response.status_code == 200

    assert response.headers['X-3scale-matched-rules'] == '/'

    assert response.headers['X-3scale-credentials'] == f"user_key={user_key}"

    assert "X-3scale-usage" in response.headers

    assert "X-3scale-hostname" in response.headers

    assert response.headers["X-3scale-service-id"] == str(service["id"])

    assert response.headers["X-3scale-service-name"] == service["system_name"]
