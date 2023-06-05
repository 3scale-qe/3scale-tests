"""
Build an apicast image containing a custom policies that fails during execution
and tests that on failed policy returns the correct error code.
"""
import backoff
import importlib_resources as resources
import pytest

from testsuite.capabilities import Capability
from testsuite.gateways import gateway
from testsuite.gateways.apicast.selfmanaged import SelfManagedApicast
from testsuite.utils import blame

pytestmark = [
    pytest.mark.required_capabilities(Capability.STANDARD_GATEWAY, Capability.CUSTOM_ENVIRONMENT),
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-6705"),
]


@pytest.fixture(scope="module")
def set_gateway_image(openshift, staging_gateway, request, testconfig):
    """
    Builds images defined by a template specified in the image template applied with parameter
    amp_release.
    oc new-app -f {image_template} --param AMP_RELEASE={amp_release}
    oc start-build {build_name}

    Adds finalizer to delete the created resources when the test ends.
    """
    openshift_client = staging_gateway.openshift
    image_stream_name = blame(request, "examplepolicy")

    github_template = resources.files("testsuite.resources.modular_apicast").joinpath("example_policy.yml")

    amp_release = openshift().image_stream_tag_from_trigger("dc/apicast-production")
    project = openshift().project_name
    build_name_github = blame(request, "apicast-example-policy-github")

    github_params = {
        "AMP_RELEASE": amp_release,
        "NAMESPACE": project,
        "BUILD_NAME": build_name_github,
        "IMAGE_STREAM_NAME": image_stream_name,
        "IMAGE_STREAM_TAG": "github",
    }

    def _delete_builds():
        openshift_client.delete_template(github_template, github_params)

    if not testconfig["skip_cleanup"]:
        request.addfinalizer(_delete_builds)

    openshift_client.new_app(github_template, github_params)
    openshift_client.start_build(build_name_github)
    return staging_gateway


# pylint: disable=unused-argument
@pytest.fixture(scope="module")
def staging_gateway(request, testconfig) -> SelfManagedApicast:
    """Deploy self-managed template based apicast gateway."""
    gw = gateway(kind=SelfManagedApicast, staging=True, name=blame(request, "gw"))
    if not testconfig["skip_cleanup"]:
        request.addfinalizer(gw.destroy)
    gw.create()
    return gw


@pytest.fixture
def policy_settings(on_failed_policy, failing_policy):
    """
    Returns the settings of the policies to be used for the gateway
    """
    return (failing_policy, on_failed_policy)


@pytest.fixture
def return_code(request) -> int:
    """returns the status code expected by the current run"""
    on_failed_conf = request.getfixturevalue("on_failed_configuration")
    return on_failed_conf.get("error_status_code", 503)


@backoff.on_predicate(backoff.fibo, lambda response: response.headers.get("server") != "openresty", max_tries=5)
def make_request(api_client):
    """Make request to the product and retry if the response isn't from APIcast"""
    return api_client.get("/")


# pylint: disable=unused-argument
def test_on_failed(set_gateway_image, application, return_code):
    """
    Sends request to backend and check that the right error_status_code is returned according
    to on_failed policy configuration.
    build_images is requested but not used to trigger the build of the image with the custom policy
    """
    api_client = application.api_client(disable_retry_status_list=(503,))

    response = make_request(api_client)
    assert response.status_code == return_code
    assert response.headers["server"] == "openresty"
