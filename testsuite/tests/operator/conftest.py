"""conftest for operator tests"""

import pytest


@pytest.fixture(scope="session")
def operator(openshift):
    """Return operator pod object."""
    pod = openshift().get_operator()
    if not pod.object_list:
        pod = openshift(project='openshift-operators').get_operator()
    return pod.object()
