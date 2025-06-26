"""
Check if annotations required by prometheus are set
"""

import pytest
from openshift_client import OpenShiftPythonException
from packaging.version import Version

from testsuite import TESTED_VERSION

pytestmark = [
    pytest.mark.sandbag,  # requires openshift
    pytest.mark.nopersistence,  # fixture saves pod name, which changes with pod redeployment
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-6509"),
    pytest.mark.skipif(TESTED_VERSION < Version("2.10"), reason="TESTED_VERSION < Version('2.10')"),
]

ANNOTATIONS = ["prometheus.io/port", "prometheus.io/scrape"]


@pytest.fixture(scope="module", params=["zync", "zync-que"])
def pod(request, openshift):
    """Return zync pod object."""
    try:
        pods = openshift().deployment(f"deployment/{request.param}").get_pods().objects()
        pod = next(filter(lambda x: x.model.status.phase == "Running", pods))
    except (StopIteration, OpenShiftPythonException):
        pods = openshift().deployment(f"dc/{request.param}").get_pods().objects()
        pod = next(filter(lambda x: x.model.status.phase == "Running", pods))
    return pod


@pytest.mark.parametrize("annotation", ANNOTATIONS)
def test_annotation_zync(annotation, pod):
    """Test annotations of zync/zync-que pod."""
    assert pod.get_annotation(annotation) is not None
