"""
Test that fapi policy fulfills Baseline profile specification.
"""

from uuid import UUID
import re
import pytest

from testsuite import rawobj
from testsuite.utils import blame


@pytest.fixture(scope="module")
def policy_settings():
    """Set policy settings"""

    return rawobj.PolicyConfig("fapi", {})


@pytest.fixture()
def custom_id(request):
    """FAPI id to be used in a request"""
    return blame(request, "fapi-id", 10)


@pytest.fixture(scope="module")
def service(service):
    """
    Set policies for the service

    policy order:
        3scale APIcast
        Fapi
        Logging
    """
    fapi_policy = rawobj.PolicyConfig("fapi", configuration={"validate_x_fapi_customer_ip_address": True})
    # fmt: off
    logging_policy = rawobj.PolicyConfig(
        "logging",
        {
            "enable_access_logs": False,
            "custom_logging":
                f'{{{{req.headers.{"x-fapi-transaction-id"}}}}}#{{{{resp.headers.{"x-fapi-transaction-id"}}}}}',
        },
    )
    # fmt: on
    service.proxy.list().policies.insert(1, fapi_policy)
    service.proxy.list().policies.insert(2, logging_policy)
    return service


@pytest.mark.parametrize(
    ("client", "gateway"),
    [("api_client", "staging_gateway"), ("prod_client", "production_gateway")],
    ids=["Staging Apicast", "Production Apicast"],
)
def test_x_fapi_header_provided(request, client, gateway, custom_id):
    """
        Test that requests on product with fapi policy returns provided x-fapi-transaction-id header
    Test:
        - Create product with fapi policy via API
        - Add logging policy, which logs "x-fapi-transaction-id" header
        - Send http GET request to endpoint / with unique header "x-fapi-transaction-id"
        - Assert that response has status code 200 and has header "x-fapi-transaction-id" matches provided id
        - Assert that x-fapi-transaction-id was logged

    """

    client = request.getfixturevalue(client)
    gateway = request.getfixturevalue(gateway)
    client = client()
    result = client.get("/", headers={"x-fapi-transaction-id": custom_id})
    fapi_id = result.headers.get("x-fapi-transaction-id")
    assert result.status_code == 200
    assert fapi_id == custom_id

    logs = gateway.get_logs()
    match = re.search(f"{custom_id}#{custom_id}", logs, re.MULTILINE)
    assert match is not None


@pytest.mark.parametrize(
    ("client", "gateway"),
    [("api_client", "staging_gateway"), ("prod_client", "production_gateway")],
    ids=["Staging Apicast", "Production Apicast"],
)
def test_x_fapi_header_created(request, client, gateway):
    """
        Test that requests on product with fapi policy returns provided x-fapi-transaction-id header
    Test:
        - Create product with fapi policy via API
        - Add logging policy, which logs "x-fapi-transaction-id" header
        - Send GET request to endpoint / without header "x-fapi-transaction-id"
        - Assert that response has status code 200
        - Assert that response has header "x-fapi-transaction-id: uuid", where uuid is
        valid uuid version 4 specified in RFC 4122
        - Assert that newly generated x-fapi-transaction-id was logged
    """
    client = request.getfixturevalue(client)
    gateway = request.getfixturevalue(gateway)
    client = client()

    result = client.get("/")
    fapi_id = result.headers.get("x-fapi-transaction-id")
    assert result.status_code == 200
    assert UUID(fapi_id).variant == "specified in RFC 4122"
    assert UUID(fapi_id).version == 4

    logs = gateway.get_logs()
    match = re.search(f"#{fapi_id}", logs, re.MULTILINE)
    assert match is not None


@pytest.mark.parametrize(
    "ip, ok",
    [("198.51.100.119", True), ("2001:db8::1:0", True), ("anything", False)],
    ids=["valid IPv4 address", "valid IPv6 address", "invalid IP address"],
)
# pylint: disable=unused-argument
def test_x_fapi_customer_ip(ip, ok, api_client):
    """
        Test that requests on product with fapi policy returns provided x-fapi-transaction-id header
    Test:
        - Create product with fapi policy via API
        - Send GET request to endpoint / with header "x-fapi-customer-ip-address"
        - Assert that response has status code 200 for valid IPv4 and IPv6 addresses
        - Assert that response status code is not 200 for invalid IP address

    """
    client = api_client()
    resp = client.get("/", headers={"x-fapi-customer-ip-address": ip})
    assert resp.ok == ok
