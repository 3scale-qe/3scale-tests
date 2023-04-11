"""conftest for operator tests"""

import pytest
from openshift import OpenShiftPythonException


@pytest.fixture(scope="session")
def operator(openshift):
    """Return operator pod object."""
    try:
        return openshift().threescale_operator
    except OpenShiftPythonException:
        return openshift(project='openshift-operators').threescale_operator
