"""
Check if annotations required by prometheus are set
"""

import pytest

from testsuite.configuration import openshift

pytestmark = [
    pytest.mark.sandbag,  # requires openshift
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-6509"),
    pytest.mark.require_version("2.10"),
]

ANNOTATIONS = [
    "prometheus.io/port", "prometheus.io/scrape"
]


@pytest.fixture(params=['dc/zync', 'dc/zync-que'])
def poda(request):
    """Return zync pod object."""
    pod = openshift().deployment(request.param).get_pods().object()
    return pod


@pytest.mark.parametrize("annotation", ANNOTATIONS)
def test_annotation_zync(annotation, poda):
    """ Test annotations of zync pod. """
    assert poda.get_annotation(annotation) is not None
