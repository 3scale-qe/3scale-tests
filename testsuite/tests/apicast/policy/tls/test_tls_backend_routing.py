""""Test for TLS Apicast with backend routing"""

import pytest
from packaging.version import Version  # noqa # pylint: disable=unused-import

from testsuite import rawobj, TESTED_VERSION  # noqa # pylint: disable=unused-import
from testsuite.capabilities import Capability
from testsuite.echoed_request import EchoedRequest
from testsuite.tests.apicast.policy.tls import embedded

pytestmark = [
    pytest.mark.required_capabilities(Capability.STANDARD_GATEWAY, Capability.CUSTOM_ENVIRONMENT),
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-8007"),
    pytest.mark.skipif("TESTED_VERSION < Version('2.12')")
]


@pytest.fixture(scope="module")
def policy_settings(certificate):
    """Sets up the embedded TLS termination policy"""
    return rawobj.PolicyConfig("tls", {"certificates": [{
        "certificate": embedded(certificate.certificate, "tls.crt", "pkix-cert"),
        "certificate_key": embedded(certificate.key, "tls.key", "x-iwork-keynote-sffkey")
    }]})


@pytest.fixture(scope="module")
def backends_mapping(custom_backend, private_base_url):
    """
    Creates four echo-api backends with the private paths being the keys in
    the dict
    """
    return {"/bar": custom_backend("backend1", endpoint=f"{private_base_url('echo_api')}/backend1"),
            "/foo/boo": custom_backend("backend2", endpoint=f"{private_base_url('echo_api')}/backend2")}


@pytest.fixture(scope="module")
def client(api_client, valid_authority):
    """Overwrite verify with correct ca"""
    client = api_client()
    client.verify = valid_authority.files["certificate"]
    return client


# pylint: disable=protected-access
def test_tls_backend_routing(client):
    """
    Preparation:
        - Creates TLS Apicast
        - Creates service with 2 backends (`/bar`, `/foo/boo`)
    Test:
        - Make request to path `bar`
        - Assert that it was routed to the right backend
        - Make request to path `/foo/boo`
        - Assert that it was routed to the right backend
    """
    for _ in range(5):
        response = client.get("/bar")
        assert response.status_code == 200
        echoed_request = EchoedRequest.create(response)
        assert echoed_request.json['path'] == '/backend1'
        response = client.get("/foo/boo")
        assert response.status_code == 200
        echoed_request = EchoedRequest.create(response)
        assert echoed_request.json['path'] == '/backend2'
