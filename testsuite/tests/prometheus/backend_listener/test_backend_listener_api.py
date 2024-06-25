"""
Testing the propagation of backend api metrics to prometheus.
When an authorization / reporting backend api endpoint is requested,
the increase of the metric, respective to the endpoint and returned
status code, is expected in prometheus.
"""

from typing import Tuple, Dict

import pytest
import requests
from packaging.version import Version  # noqa # pylint: disable=unused-import

from testsuite.rhsso.rhsso import OIDCClientAuthHook
from testsuite.utils import blame, randomize
from testsuite import rawobj, TESTED_VERSION  # noqa # pylint: disable=unused-import

NUM_OF_REQUESTS = 10

pytestmark = [
    # can not be run in parallel
    pytest.mark.disruptive,
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-4641"),
    pytest.mark.skipif("TESTED_VERSION < Version('2.10')"),
]


@pytest.fixture(scope="module")
def lifecycle_hooks_oauth(request, testconfig):
    """
    List of objects with hooks into app/svc creation and deletion

    Hooks should implement methods defined and documented in testsuite.lifecycle_hook.LifecycleHook
    or should inherit from that class
    """
    defaults = testconfig.get("fixtures", {}).get("lifecycle_hooks", {}).get("defaults")
    if defaults is not None:
        return [request.getfixturevalue(i) for i in defaults]
    return []


@pytest.fixture(scope="module", autouse=True)
def rhsso_setup(lifecycle_hooks_oauth, rhsso_service_info):
    """
    Setting up the oath for the service using the lifecycle_hooks_oauth
    """
    lifecycle_hooks_oauth.append(OIDCClientAuthHook(rhsso_service_info, credentials_location="query"))


@pytest.fixture(scope="module")
def service_oauth(backends_mapping, custom_service, request, service_proxy_settings, lifecycle_hooks_oauth):
    """
    Service secured with oauth
    """
    return custom_service(
        {"name": blame(request, "svc")}, service_proxy_settings, backends_mapping, hooks=lifecycle_hooks_oauth
    )


@pytest.fixture(scope="module")
def application_oauth(service_oauth, custom_application, custom_app_plan, lifecycle_hooks_oauth):
    """
    Application using service secured with oauth
    """
    plan = custom_app_plan(rawobj.ApplicationPlan(randomize("AppPlan")), service_oauth)
    return custom_application(rawobj.Application(randomize("App"), plan), hooks=lifecycle_hooks_oauth)


@pytest.fixture(scope="module")
def token(application_oauth, rhsso_service_info):
    """
    Access token for 3scale application that is connected with RHSSO
    """
    return rhsso_service_info.access_token(application_oauth)


@pytest.fixture(scope="module")
def oauth_service_token(application_oauth):
    """
    Service token of the application using oauth
    """
    return application_oauth.service.proxy.list().configs.list(env="sandbox")[0]["proxy_config"]["content"][
        "backend_authentication_value"
    ]


@pytest.fixture(scope="module")
def oauth_params(service_oauth, oauth_service_token, token, application_oauth):
    """
    Returns two sets of parameters for an application using oauth authentication.
    The former producing 2xx request, the later unauthorized 403 request
    """
    return {
        "params": {
            "service_token": oauth_service_token,
            "service_id": service_oauth.entity_id,
            "app_id": application_oauth["application_id"],
            "access_token": token,
        }
    }, {"params": {}}


@pytest.fixture(scope="module")
def standard_auth(service, service_token, application):
    """
    Returns two sets of parameters for an application using standard authentication.
    The former producing 2xx request, the later unauthorized 403 request
    """
    return {
        "params": {
            **{"service_token": service_token, "service_id": service.entity_id},
            **application.authobj().credentials,
        }
    }, {"params": {}}


@pytest.fixture(scope="module")
def transaction_auth(service, service_token, application):
    """
    Returns two sets of parameters for a call to reporting endpoint ("/transactions.xml"),
    where the auth information has to be passed as data
    The former producing 2xx request, the later 403 request
    """
    return {
        "data": {
            "service_token": service_token,
            "service_id": service.entity_id,
            "transactions[0][usage][hits]": "1",
            "transactions[0][user_key]": application.authobj().credentials["user_key"],
        }
    }, {"data": {}}


@pytest.fixture(scope="function")
def auth_request(backend_listener_url):
    """
    Makes request to backend listener using provided endpoint and passing authentication
    as defined
    """

    def _auth_request(method, endpoint, auth_object):
        formatted_endpoint = backend_listener_url + "/transactions" + endpoint
        return requests.request(method, formatted_endpoint, **auth_object[0]), requests.request(
            method, formatted_endpoint, **auth_object[1]
        )

    return _auth_request


def authrep_backend_api_query(request_type) -> Tuple[str, Dict[str, str]]:
    """
    Returns prometheus query parts for the apisonator_listener_response_codes metric
    with the request type passed in the parameters
    """
    return "apisonator_listener_response_codes", {"request_type": request_type}


@pytest.fixture(scope="module")
def data(standard_auth, transaction_auth, oauth_params):
    """
    Data for testing
    For each prometheus metric, there is a 3-tuple of method, endpoint and authentication to be used.
    Not using parametrized testcase to avoid waiting 30s for prometheus to load metrics for each testcase
    """
    return {
        "authorize": ("GET", "/authorize.xml", standard_auth),
        "authrep": ("GET", "/authrep.xml", standard_auth),
        "report": ("POST", ".xml", transaction_auth),
        "authorize_oauth": ("GET", "/oauth_authorize.xml", oauth_params),
        "authrep_oauth": ("GET", "/oauth_authrep.xml", oauth_params),
    }


# pylint: disable=too-many-locals
def test_authrep(data, prometheus_response_codes_for_metric, auth_request, prometheus):
    """
    Sends NUM_OF_REQUESTS requests returning 2xx response and 403 response
    to each backend-listener authorization endpoint.

    Asserts that the metrics for the number of requests to the particular endpoint
    for the particular response code has increased in prometheus.
    """

    # wait to update metrics triggered by previous tests
    prometheus.wait_on_next_scrape("backend-listener")

    count_before = {}
    for request_type in data:
        key, labels = authrep_backend_api_query(request_type)
        count_before[request_type] = prometheus_response_codes_for_metric(key, labels)
        method, endpoint, params = data[request_type]
        for _ in range(NUM_OF_REQUESTS):
            response_2xx, response_403 = auth_request(method, endpoint, params)
            assert response_2xx.status_code in {200, 202}
            assert response_403.status_code == 403, f"failed for {request_type}"

    # wait for prometheus to collect the metrics
    prometheus.wait_on_next_scrape("backend-listener")

    count_after = {}
    results = {}

    for request_type in data:
        key, labels = authrep_backend_api_query(request_type)
        count_after[request_type] = prometheus_response_codes_for_metric(key, labels)
        for response_code in ["2xx", "403"]:
            results[request_type + response_code] = response_code in count_after[request_type] and (
                (
                    response_code not in count_before[request_type]
                    and int(count_after[request_type][response_code]) == NUM_OF_REQUESTS
                )
                or int(count_after[request_type][response_code]) - int(count_before[request_type][response_code])
                == NUM_OF_REQUESTS
            )

    for request_type_response_code in results.values():
        assert request_type_response_code, f"{results}"
