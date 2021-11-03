"""
Build an apicast image containing a custom policies that fails during execution
and tests that on failed policy returns the correct error code.
"""

import pytest
import importlib_resources as resources


from testsuite.capabilities import Capability
from testsuite.gateways import TemplateApicastOptions, TemplateApicast
from testsuite.utils import blame


pytestmark = [pytest.mark.required_capabilities(Capability.STANDARD_GATEWAY),
              pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-6705")]


@pytest.fixture(scope="module")
def image_stream_amp_apicast_custom_policy(request):
    """
    Returns the blamed name for the amp-apicast-custom-policy image stream
    """
    return blame(request, "is-amp-apicast-custom-policy")


@pytest.fixture(scope="module")
def build_images(openshift, request, image_stream_amp_apicast_custom_policy):
    """
    Builds images defined by a template specified in the image template applied with parameter
    amp_release.
    oc new-app -f {image_template} --param AMP_RELEASE={amp_release}
    oc start-build {build_name}

    Adds finalizer to delete the created resources when the test ends.
    """
    openshift_client = openshift()

    amp_release = openshift_client.image_stream_tag("amp-apicast")
    build_name_failing_policy = blame(request, "apicast-failing-policy")
    build_name_custom_policies = blame(request, "apicast-custom-policies")
    image_stream_apicast_policy = blame(request, "is-apicast-policy")
    image_template = resources.files('testsuite.resources.on_failed_policy').joinpath("apicast_failing_policy.yml")

    template_params = {"AMP_RELEASE": amp_release,
                       "BUILD_NAME_FAILING_POLICY": build_name_failing_policy,
                       "BUILD_NAME_CUSTOM_POLICY": build_name_custom_policies,
                       "IMAGE_STREAM_APICAST_POLICY": image_stream_apicast_policy,
                       "IMAGE_STREAM_AMP_APICAST_CUSTOM_POLICY": image_stream_amp_apicast_custom_policy
                       }

    request.addfinalizer(lambda: openshift_client.delete_template(image_template, template_params))

    openshift_client.new_app(image_template, template_params)
    openshift_client.start_build(build_name_failing_policy)


@pytest.fixture(scope="module")
def staging_gateway(request, configuration, settings_block,
                    image_stream_amp_apicast_custom_policy) -> TemplateApicast:
    """Deploy an apicast gateway with custom image from image_stream_amp_apicast_custom_policy"""

    options = TemplateApicastOptions(staging=True, settings_block=settings_block, configuration=configuration)
    gateway = TemplateApicast(requirements=options)

    request.addfinalizer(gateway.destroy)

    gateway.create()

    gateway.update_image_stream(image_stream_amp_apicast_custom_policy)
    return gateway


@pytest.fixture
def policy_settings(on_failed_policy, failing_policy):
    """
    Returns the settings of the policies to be used for the gateway
    """
    return (failing_policy, on_failed_policy)


@pytest.fixture
def return_code(request) -> int:
    """returns the status code expected by the current run"""
    on_failed_conf = request.getfixturevalue('on_failed_configuration')
    return on_failed_conf.get("error_status_code", 503)


# pylint: disable=unused-argument
def test_on_failed(build_images, application, return_code):
    """
    Sends request to backend and check that the right error_status_code is returned according
    to on_failed policy configuration.
    build_images is requested but not used to trigger the build of the image with the custom policy
    """
    api_client = application.api_client(disable_retry_status_list=(503,))

    response = api_client.get("/")
    assert response.status_code == return_code
