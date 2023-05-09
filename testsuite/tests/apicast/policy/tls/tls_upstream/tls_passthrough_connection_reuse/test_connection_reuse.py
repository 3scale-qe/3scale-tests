"""
Tests, that the ssl connection is not reused for different backends.
Tests thet when the backends are connected with openshift routes using the passthrough tls policy,
the first estabilished connection is not reused for all requests to the same IP, that being
the Openshift HAProxy router, and the requests are routed to the appropriate backend.
"""

import pytest

from packaging.version import Version  # noqa # pylint: disable=unused-import
from testsuite import TESTED_VERSION  # noqa # pylint: disable=unused-import
from testsuite.echoed_request import EchoedRequest

pytestmark = [
    pytest.mark.nopersistence,
    pytest.mark.skipif("TESTED_VERSION < Version('2.11')"),
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-6849"),
]


@pytest.fixture(scope="module")
def authority_and_code(valid_authority):
    """
    Returns authority for httpbin and return code it should return
    For the testing of connection reuse is just one valid authority sufficient.
    """
    return valid_authority, 200


# pylint: disable=unused-argument
def test_connection_reuse(api_client, mapping_rules):
    """
    - Have two backend httpbins with TLS enabled and with TLS passthrough routes.
    - Have a product in 3scale with two backends with different mapping rules
      whose upstream APIs are the httpbins.
    - Have the mTLS policy between APIcast and the backend APIs established.
    - Send requests routed to the first and second backend, to the '/info' httpbin endpoint,
      which returns the information about the httpbin.
    - Assert that each request got routed to the appropriate backend using the information returned
      in the '/info' request (info['tls']['ServerName']).
      (The second request should not use the established TLS connection between the APIcast and
       the first backend)

    """
    client = api_client()

    response_orig = client.get("/orig/info")
    response_new = client.get("/new/info")

    assert response_orig.status_code == 200
    assert response_new.status_code == 200

    info_orig = EchoedRequest.create(response_orig)
    info_new = EchoedRequest.create(response_new)

    assert info_orig.json["tls"]["ServerName"] != info_new.json["tls"]["ServerName"]
