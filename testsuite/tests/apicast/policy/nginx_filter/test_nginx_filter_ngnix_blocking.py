"""
When the APIcast is has enabled content caching, it blocks requests from certain upstreams that contain If-Match header
with 412 response code.
The nginx filter policy should ensure that those requests will not be blocked.
"""


import pytest
from packaging.version import Version  # noqa # pylint: disable=unused-import

from testsuite import rawobj, TESTED_VERSION  # noqa # pylint: disable=unused-import
from testsuite.utils import blame

pytestmark = [
    pytest.mark.skipif("TESTED_VERSION < Version('2.11')"),
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-6704"),
]


@pytest.fixture(
    scope="module",
    params=[
        (None, 412),
        pytest.param(
            (True, 200),
            marks=[pytest.mark.xfail, pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-7514")],
        ),
        (False, 200),
    ],
)
def append_settings_and_expected_response(request):
    """
    Parametrization of the policy setting.
    The first case ensures that the configuration is correct and the request is blocked without the policy.
    The second and third case assert that when the policy is set up, APIcast does not block the request based on
    the header.
    """
    return request.param[0], request.param[1]


@pytest.fixture(scope="module")
# pylint: disable=unused-argument
def service_settings(request, append_settings_and_expected_response):
    """
    Parametrization of service_settings to blame new name for each new service
    to avoid naming collisions
    """
    return {"name": blame(request, "svc")}


@pytest.fixture(scope="module")
def service(service, append_settings_and_expected_response):
    """
    Sets caching policy to set up an environment, where APIcast returns 412 on request containing If-Match header.

    Sets the nginx http://echo service as upstream, as all upstreams the testsuite is using are behind the
    Openshift router which adds the "cache-control: private" header that causes the APIcast not to return the 412.

    Sets the nginx filter policy based on the parametrization.
    """
    append, _ = append_settings_and_expected_response

    proxy = service.proxy.list()
    proxy.policies.insert(
        1,
        rawobj.PolicyConfig(
            "content_caching",
            {
                "rules": [
                    {
                        "cache": True,
                        "header": "X-Cache-Status",
                        "condition": {"combine_op": "and", "operations": [{"left": "oo", "op": "==", "right": "oo"}]},
                    }
                ]
            },
        ),
    )

    proxy.policies.insert(0, rawobj.PolicyConfig("upstream", {"rules": [{"url": "http://echo", "regex": "/"}]}))

    if append is not None:
        proxy.policies.insert(
            2, rawobj.PolicyConfig("nginx_filters", {"headers": [{"name": "If-Match", "append": append}]})
        )

    return service


def test_if_match_append(api_client, append_settings_and_expected_response):
    """
    Asserts that the request is evaluated correctly by APIcast based on the passed settings.
    """
    _, expected_response_code = append_settings_and_expected_response
    client = api_client()
    response = client.get("/", headers={"If-Match": "Anything"})
    assert response.status_code == expected_response_code
