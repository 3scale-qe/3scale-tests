"""
Tests that an apicast image containing custom policies can be build,
substituted for the image of the deployed apicast and the custom policies
are working as expected.
"""

import backoff

import pytest
import importlib_resources as resources
from testsuite import rawobj
from testsuite.capabilities import Capability
from testsuite.utils import blame

pytestmark = [pytest.mark.required_capabilities(Capability.STANDARD_GATEWAY),
              pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-553")]


@pytest.fixture(scope="module")
def image_stream_name(request):
    """
    Returns the blamed name for the amp-apicast-custom-policy image stream
    """
    return blame(request, "examplepolicy")


@pytest.fixture(scope="module")
def build_images(openshift, request, image_stream_name):
    """
    Builds images defined by a template specified in the image template applied with parameter
    amp_release.
    oc new-app -f {image_template} --param AMP_RELEASE={amp_release}
    oc start-build {build_name}

    Adds finalizer to delete the created resources when the test ends.
    """
    openshift_client = openshift()

    github_template = resources.files('testsuite.resources.modular_apicast').joinpath("example_policy.yml")
    copy_template = resources.files('testsuite.resources.modular_apicast').joinpath("example_policy_copy.yml")

    amp_release = openshift_client.image_stream_tag_from_trigger("dc/apicast-production")
    build_name_github = blame(request, "apicast-example-policy-github")
    build_name_copy = blame(request, "apicast-example-policy-copy")

    github_params = {"AMP_RELEASE": amp_release,
                     "BUILD_NAME": build_name_github,
                     "IMAGE_STREAM_NAME": image_stream_name,
                     "IMAGE_STREAM_TAG": "github"}

    copy_params = {"AMP_RELEASE": amp_release,
                   "BUILD_NAME": build_name_copy,
                   "TARGET_IMAGE_STREAM": image_stream_name,
                   "TARGET_TAG": "latest",
                   "EXAMPLE_POLICY_IMAGE_STREAM": image_stream_name,
                   "EXAMPLE_POLICY_TAG": "github"}

    def _delete_builds():
        openshift_client.delete_template(github_template, github_params)
        openshift_client.delete_template(copy_template, copy_params)

    request.addfinalizer(_delete_builds)

    openshift_client.new_app(github_template, github_params)
    openshift_client.new_app(copy_template, copy_params)
    openshift_client.start_build(build_name_github)
    openshift_client.start_build(build_name_copy)


@pytest.fixture(scope="module")
def staging_gateway(staging_gateway, image_stream_name):
    """
    Deploys template apicast.
    Updates the gateway to use the new imagestream.
    """
    staging_gateway.update_image_stream(image_stream_name)
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
@backoff.on_predicate(backoff.fibo, lambda x: "X-Example-Policy-Response" not in x.headers, 8, jitter=None)
def get(api_client, url):
    """Resilient get to ensure apicast has time to initialize policy chain"""
    return api_client.get(url)


# pylint: disable=unused-argument
def test_modular_apicast(build_images, api_client):
    """
    Sends a request.
    Asserts that the header added by the example policy is present.
    """
    response = get(api_client(), "/")
    assert response.status_code == 200
    assert 'X-Example-Policy-Response' in response.headers
