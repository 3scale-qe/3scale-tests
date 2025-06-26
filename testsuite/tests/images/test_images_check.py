"""Image checkt tests"""

import pytest

from packaging.version import Version

from openshift_client import OpenShiftPythonException

from testsuite.gateways import gateway
from testsuite.gateways.apicast.operator import OperatorApicast
from testsuite.utils import blame
from testsuite import TESTED_VERSION


pytestmark = pytest.mark.nopersistence


PARAMETERS = [
    ("threescale_system", "amp-system", ["system-app", "system-sidekiq"], []),
    ("threescale_backend", "amp-backend", ["backend-listener", "backend-worker", "backend-cron"], []),
    ("threescale_zync", "amp-zync", ["zync", "zync-que"], []),
    (
        "threescale_memcached",
        "system-memcached",
        ["system-memcache"],
        [pytest.mark.skipif("TESTED_VERSION > Version('2.15.0')")],
    ),
    ("threescale_searchd", "system-searchd", ["system-searchd"], []),
    ("apicast", "amp-apicast", ["apicast-staging", "apicast-production"], []),
]


IS_PARAMETERS = [pytest.param(image, image_stream, marks=marks) for image, image_stream, _, marks in PARAMETERS]
COMPONENTS_PARAMETERS = [
    pytest.param(image, deployment_configs, marks=marks) for image, _, deployment_configs, marks in PARAMETERS
]


@pytest.mark.parametrize(("image", "image_stream"), IS_PARAMETERS)
# INFO: image streams are no longer used (starting with 2.15-dev)
@pytest.mark.skipif(TESTED_VERSION > Version("2.14"), reason="TESTED_VERSION > Version('2.14')")
def test_imagesource_image(images, openshift, image, image_stream):
    """
    Test:
        - load expected images from settings
        - assert that expected image and image in image stream are the same
        - assert that expected image and image in deployment config are the same
    """
    expected_image = images[image]
    openshift = openshift()
    lookup = openshift.do_action("get", [f"is/{image_stream}", "-o", "yaml"], parse_output=True)
    digest = lookup.model.spec.tags[-1]["from"].name.split(":")[-1]
    assert digest == expected_image["manifest_digest"]


@pytest.mark.parametrize(("image", "deployment_configs"), COMPONENTS_PARAMETERS)
def test_deployment_image(images, openshift, image, deployment_configs):
    """
    Test:
        - load expected images from settings
        - assert that expected image and image in deployment config are the same
    """
    expected_image = "UNKNOWN"
    openshift = openshift()

    for deployment_config in deployment_configs:
        try:
            expected_image = images[image]["resolved_images"].get(openshift.arch)
            lookup = openshift.do_action("get", [f"dc/{deployment_config}", "-o", "yaml"], parse_output=True)
        except (StopIteration, OpenShiftPythonException):
            expected_image = images[image]["manifest_digest"]
            lookup = openshift.do_action("get", [f"deployment/{deployment_config}", "-o", "yaml"], parse_output=True)

        for container in lookup.model.spec.template.spec.containers:
            digest = container.image.split(":")[-1]
            assert digest == expected_image


@pytest.fixture(scope="module")
def staging_gateway(request, testconfig):
    """Deploy self-managed template based apicast gateway."""
    gw = gateway(kind=OperatorApicast, staging=True, name=blame(request, "gw"))
    if not testconfig["skip_cleanup"]:
        request.addfinalizer(gw.destroy)
    gw.create()
    return gw


def test_apicast_image(images, staging_gateway):
    """
    Test:
        - load expected image from yaml file
        - load deployed image from apicast deployment
        - assert that expected and deployed images are the same
    """
    expected_image = images["apicast"]
    lookup = staging_gateway.openshift.do_action(
        "get", [staging_gateway.deployment.resource, "-o", "yaml"], parse_output=True
    )
    digest = lookup.model.spec.template.spec.containers[0].image.split(":")[-1]
    assert digest == expected_image["manifest_digest"]


@pytest.mark.parametrize("operator_type", ["operator", "apicast_operator"])
def test_operator_image(images, operator_type, request):
    """
    Test:
        - load expected image from settings
        - load deployed image from operator deployment
        - assert that expected and deployed images are the same
    """
    expected_image = images[operator_type]
    operator = request.getfixturevalue(operator_type)
    digest = operator.model.spec.containers[0].image.split(":")[-1]
    assert digest == expected_image
