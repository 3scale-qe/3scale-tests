"""
Test that fapi policy fulfills Baseline profile specification.
"""

import re
import warnings
from uuid import UUID

import pytest
import threescale_api
from packaging.version import Version

from testsuite import TESTED_VERSION, rawobj
from testsuite.utils import blame

pytestmark = pytest.mark.skipif(TESTED_VERSION < Version("2.16"), reason="Threescale version must be at least 2.16.0")


@pytest.fixture(scope="module")
def prod_client(production_gateway, application, request, testconfig):
    """
    Duplicate with different scope, the reasoning behind duplicate is that if called prod_client from root conftest
    it didn't behave as expected.
    Prepares application and service for production use and creates new production client

    Parameters:
        app (Application): Application for which create the client.
        promote (bool): If true, then this method also promotes proxy configuration to production.
        version (int): Proxy configuration version of service to promote.
        redeploy (bool): If true, then the production gateway will be reloaded

    Returns:
        api_client (HttpClient): Api client for application

    """

    def _prod_client(app=application, promote: bool = True, version: int = -1, redeploy: bool = True):
        if promote:
            if version == -1:
                version = app.service.proxy.list().configs.latest()["version"]
            try:
                app.service.proxy.list().promote(version=version)
            except threescale_api.errors.ApiClientError as err:
                warnings.warn(str(err))
                redeploy = False

        if redeploy:
            production_gateway.reload()

        client = app.api_client(endpoint="endpoint")
        if hasattr(client, "close"):
            if not testconfig["skip_cleanup"]:
                request.addfinalizer(client.close)
        return client

    return _prod_client


@pytest.fixture(scope="module")
def policy_settings():
    """Set policy settings"""
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
    return [fapi_policy, logging_policy]


@pytest.fixture()
def custom_id(request):
    """FAPI id to be used in a request"""
    return blame(request, "fapi-id", 10)


@pytest.fixture()
def service_config_version(service):
    """get version of latest change"""
    return service.proxy.list().configs.latest()["version"]


@pytest.mark.parametrize("provide_fapi_id", [False, True], ids=["no_fapi_id", "fapi_id"])
@pytest.mark.parametrize(
    ("client", "gateway"),
    [
        ("api_client", "staging_gateway"),
        pytest.param("prod_client", "production_gateway", marks=pytest.mark.disruptive),
    ],
    ids=["staging_apicast", "production_apicast"],
)
# pylint: disable=too-many-arguments
def test_x_fapi_header(request, client, gateway, provide_fapi_id, custom_id, service_config_version):
    """
        Test that requests on product with fapi policy returns provided x-fapi-transaction-id header
    Test:
        - Create product with fapi policy via API
        - Add logging policy, which logs "x-fapi-transaction-id" header
        - Send http GET request to endpoint / with unique header "x-fapi-transaction-id"
        - Assert that response has status code 200 and has header "x-fapi-transaction-id" matches provided id
        - Assert that x-fapi-transaction-id was logged
        - Send GET request to endpoint / without header "x-fapi-transaction-id"
        - Assert that response has status code 200
        - Assert that response has header "x-fapi-transaction-id: uuid", where uuid is
        valid uuid version 4 specified in RFC 4122
        - Assert that newly generated x-fapi-transaction-id was logged

    """
    client_kwargs = {}
    if client == "prod_client":
        client_kwargs = {"version": service_config_version}

    client = request.getfixturevalue(client)
    gateway = request.getfixturevalue(gateway)
    client = client(**client_kwargs)

    headers = None
    if provide_fapi_id:
        headers = {"x-fapi-transaction-id": custom_id}

    result = client.get("/", headers=headers)
    fapi_id = result.headers.get("x-fapi-transaction-id")
    assert result.status_code == 200
    if provide_fapi_id:
        # test whether apicast returns same x-fapi-transaction-id
        assert fapi_id == custom_id
    else:
        # test whether apicast generates new x-fapi-transaction-id
        assert UUID(fapi_id).variant == "specified in RFC 4122"
        assert UUID(fapi_id).version == 4
    logs = gateway.get_logs()
    match = re.search(f"{custom_id if provide_fapi_id else ''}#{fapi_id}", logs, re.MULTILINE)
    assert match is not None


@pytest.mark.parametrize("provide_fapi_id", [False, True], ids=["no_fapi_id", "fapi_id"])
@pytest.mark.parametrize(
    "ip, ok",
    [("198.51.100.119", True), ("2001:db8::1:0", True), ("jggorpesuogojyib", False)],
    ids=["valid_IPv4_address", "valid_IPv6_address", "invalid_IP_address"],
)
# pylint: disable=unused-argument
def test_x_fapi_customer_ip(ip, ok, api_client, provide_fapi_id, custom_id):
    """
        Test that requests on product with fapi policy returns provided x-fapi-transaction-id header
    Test:
        - Create product with fapi policy via API
        - Send GET request to endpoint / with header "x-fapi-customer-ip-address" and "x-fapi-transaction-id"
        - Assert that response has status code 200 for valid IPv4 and IPv6 addresses
        - Assert that response status code is not 200 for invalid IP address
        - Assert that "x-fapi-transaction-id" stayed the same when was provided and was generated when wasn't provided

    """
    headers = {"x-fapi-customer-ip-address": ip}
    if provide_fapi_id:
        headers.update({"x-fapi-transaction-id": custom_id})
    client = api_client()
    resp = client.get("/", headers=headers)
    assert resp.ok == ok
    fapi_id = resp.headers.get("x-fapi-transaction-id")
    if provide_fapi_id:
        assert fapi_id == custom_id
    else:
        assert UUID(fapi_id).variant == "specified in RFC 4122"
        assert UUID(fapi_id).version == 4
