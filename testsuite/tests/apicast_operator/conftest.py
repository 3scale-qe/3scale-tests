"""conftest for apicast-operator tests"""

import pytest

from testsuite import settings


@pytest.fixture(scope="session")
def operator(openshift):
    """Return operator pod object."""

    def select_operator(apiobject):
        return apiobject.get_label("app") == "apicast" and apiobject.get_label("control-plane") == "controller-manager"

    project_name = settings["threescale"]["gateway"]["OperatorApicast"]['openshift']['project_name']

    pod = openshift(project=project_name, server="OperatorApicast")\
        .select_resource("pods", narrow_function=select_operator)
    if not pod.object_list:
        pod = openshift(project='openshift-operators', server="OperatorApicast")\
            .select_resource("pods", narrow_function=select_operator)
    return pod.object()
