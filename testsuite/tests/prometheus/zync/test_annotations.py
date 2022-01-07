"""
Check if annotations required by prometheus are set
"""

import pytest
from packaging.version import Version  # noqa # pylint: disable=unused-import

from testsuite import TESTED_VERSION  # noqa # pylint: disable=unused-import
from testsuite.configuration import openshift

pytestmark = [
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-6509"),
    pytest.mark.skipif("TESTED_VERSION < Version('2.10')"),
]

ANNOTATIONS = [
    "prometheus.io/port", "prometheus.io/scrape"
]


@pytest.fixture(params=['zync', 'zync-que'])
def poda(request):
    """Return zync pod object."""
    pod = openshift().get_pod(request.param).object()
    return pod


@pytest.mark.parametrize("annotation", ANNOTATIONS)
def test_annotation_zync(annotation, poda):
    """ Test annotations of zync pod. """
    assert poda.get_annotation(annotation) is not None
