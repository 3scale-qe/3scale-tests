"""Image checkt tests"""
import pytest

from testsuite.gateways import gateway
from testsuite.gateways.apicast.operator import OperatorApicast
from testsuite.utils import blame

pytestmark = pytest.mark.nopersistence


@pytest.mark.parametrize(
    ("image", "image_stream", "deployment_configs"),
    [("threescale_system", "amp-system", ["system-app"]),
     ("threescale_backend", "amp-backend", ["backend-worker"]),
     ("threescale_zync", "amp-zync", ["zync"]),
     ("threescale_memcached", "system-memcached", ["system-memcache"]),
     ("apicast", "amp-apicast", ["apicast-staging", "apicast-production"])])
def test_deployment_image(images, openshift, image, image_stream, deployment_configs):
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
    for deployment_config in deployment_configs:
        lookup = openshift.do_action("get", [f"dc/{deployment_config}", "-o", "yaml"], parse_output=True)
        for container in lookup.model.spec.template.spec.containers:
            digest = container.image.split(":")[-1]
            assert digest == expected_image["resolved_images"].get(openshift.arch)


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
    lookup = staging_gateway.openshift.do_action("get", [staging_gateway.deployment.resource, "-o", "yaml"],
                                                 parse_output=True)
    digest = lookup.model.spec.template.spec.containers[0].image.split(":")[-1]
    assert digest == expected_image["manifest_digest"]


@pytest.fixture(scope="module")
def apicast_operator(staging_gateway):
    """return: Self-managed Apicast operator"""
    return staging_gateway.openshift.get_apicast_operator().object()


@pytest.fixture(scope="module")
def threescale_operator(openshift):
    """return: 3scale operator"""
    return openshift().get_operator().object()


@pytest.mark.parametrize("operator_type", ["threescale_operator", "apicast_operator"])
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
