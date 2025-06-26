"""
Tests that an apicast custom policy with lua dependency can be built and used
"""

import importlib_resources as resources
import pytest

# pylint: disable=no-name-in-module, c-extension-no-member
# pylint has problem with lxml for some reason
from lxml import etree
from lxml.etree import XMLSyntaxError
from openshift_client import OpenShiftPythonException

from testsuite import rawobj
from testsuite.capabilities import Capability
from testsuite.gateways.apicast.operator import OperatorApicast
from testsuite.gateways.apicast.template import TemplateApicast
from testsuite.utils import blame, warn_and_skip

pytestmark = [
    pytest.mark.required_capabilities(Capability.STANDARD_GATEWAY, Capability.CUSTOM_ENVIRONMENT),
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-7488"),
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
    image_stream_name = blame(request, "xml_policy")

    template = resources.files("testsuite.resources.modular_apicast").joinpath("xml_policy.yml")

    try:
        amp_release = openshift().image_stream_tag_from_trigger("dc/apicast-production")
    except OpenShiftPythonException:
        warn_and_skip("ImageStream is not avaiable after 2.14-dev, templates are no longer supported")

    project = openshift().project_name
    build_name = blame(request, "apicast-xml-policy")

    params = {
        "AMP_RELEASE": amp_release,
        "NAMESPACE": project,
        "BUILD_NAME": build_name,
        "IMAGE_STREAM_NAME": image_stream_name,
        "IMAGE_STREAM_TAG": "latest",
    }

    def _delete_builds():
        openshift_client.delete_template(template, params)

    if not testconfig["skip_cleanup"]:
        request.addfinalizer(_delete_builds)

    openshift_client.new_app(template, params)
    openshift_client.start_build(build_name)

    staging_gateway.set_image(f"{openshift_client.image_stream_repository(image_stream_name)}:latest")


@pytest.fixture(scope="module")
def policy_settings():
    """
    Enables the example policy - a custom policy present in the newly built apicast image.
    """
    return rawobj.PolicyConfig("json_to_xml", configuration={})


@pytest.fixture(scope="module")
def service(service, policy_settings):
    """
    Service with prepared policy_settings added.
    """
    service.proxy.list().policies.append(policy_settings)
    return service


# pylint: disable=unused-argument
def test_modular_apicast(set_gateway_image, api_client):
    """
    Sends a request.
    Asserts that the response body is XML.
    """
    response = api_client().get("/get")
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/xml"
    try:
        etree.fromstring(response.content)
    except XMLSyntaxError as exc:
        assert False, f"Response body is not a correct XML, {exc}"
