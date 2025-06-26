"""
Tests that an apicast image containing custom policies can be build,
substituted for the image of the deployed apicast and the custom policies
are working as expected.

When tested with APIcast deployed by template it successfully tests custom policies,
 however for Operator it does test APIcast with custom image only as the supported way of doing custom policies
 through operator is a different one.
"""

import backoff
import importlib_resources as resources
import pytest
from openshift_client import OpenShiftPythonException

from testsuite import rawobj
from testsuite.capabilities import Capability
from testsuite.gateways.apicast.operator import OperatorApicast
from testsuite.gateways.apicast.template import TemplateApicast
from testsuite.utils import blame, warn_and_skip

pytestmark = [
    pytest.mark.required_capabilities(Capability.STANDARD_GATEWAY, Capability.CUSTOM_ENVIRONMENT),
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-553"),
    pytest.mark.sandbag,
]  # explicit requirement of operator apicast - doesn't have to be available


@pytest.fixture(
    scope="module",
    params=[
        pytest.param(
            TemplateApicast,
            id="Custom policy test (Template)",
            marks=[pytest.mark.required_capabilities(Capability.OCP3)],
        ),
        pytest.param(
            OperatorApicast,
            id="Custom image test (Operator)",
            marks=[pytest.mark.required_capabilities(Capability.OCP4)],
        ),
    ],
)
def gateway_kind(request):
    """Gateway class to use for tests"""
    return request.param


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
    copy_template = resources.files("testsuite.resources.modular_apicast").joinpath("example_policy_copy.yml")

    try:
        amp_release = openshift().image_stream_tag_from_trigger("dc/apicast-production")
    except OpenShiftPythonException:
        warn_and_skip("ImageStream is not avaiable after 2.14-dev, templates are no longer supported")

    project = openshift().project_name
    build_name_github = blame(request, "apicast-example-policy-github")
    build_name_copy = blame(request, "apicast-example-policy-copy")

    github_params = {
        "AMP_RELEASE": amp_release,
        "NAMESPACE": project,
        "BUILD_NAME": build_name_github,
        "IMAGE_STREAM_NAME": image_stream_name,
        "IMAGE_STREAM_TAG": "github",
    }

    copy_params = {
        "AMP_RELEASE": amp_release,
        "NAMESPACE": project,
        "BUILD_NAME": build_name_copy,
        "TARGET_IMAGE_STREAM": image_stream_name,
        "TARGET_TAG": "latest",
        "EXAMPLE_POLICY_IMAGE_STREAM": image_stream_name,
        "EXAMPLE_POLICY_TAG": "github",
    }

    def _delete_builds():
        openshift_client.delete_template(github_template, github_params)
        openshift_client.delete_template(copy_template, copy_params)

    if not testconfig["skip_cleanup"]:
        request.addfinalizer(_delete_builds)

    openshift_client.new_app(github_template, github_params)
    openshift_client.new_app(copy_template, copy_params)
    openshift_client.start_build(build_name_github)
    openshift_client.start_build(build_name_copy)

    staging_gateway.set_image(f"{openshift_client.image_stream_repository(image_stream_name)}:latest")
    return staging_gateway


@pytest.fixture(scope="module")
def policy_settings():
    """
    Enables the example policy - a custom policy present in the newly built apicast image.
    """
    return rawobj.PolicyConfig("example", configuration={}, version="0.1")


@pytest.fixture(scope="module")
def service(service, policy_settings):
    """
    Service with prepared policy_settings added.
    """
    service.proxy.list().policies.append(policy_settings)
    return service


# for some reason first requests do not seem to be modified, policy is applied later
@backoff.on_predicate(backoff.fibo, lambda x: "X-Example-Policy-Response" not in x.headers, max_tries=8, jitter=None)
def get(api_client, url):
    """Resilient get to ensure apicast has time to initialize policy chain"""
    return api_client.get(url)


# pylint: disable=unused-argument
def test_modular_apicast(set_gateway_image, api_client):
    """
    Sends a request.
    Asserts that the header added by the example policy is present.
    """
    response = get(api_client(), "/")
    assert response.status_code == 200
    assert "X-Example-Policy-Response" in response.headers
