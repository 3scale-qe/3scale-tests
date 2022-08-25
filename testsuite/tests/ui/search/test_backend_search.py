"""
Test for backend search
"""
import pytest

from testsuite.ui.views.admin.backend import BackendsView
from testsuite.utils import blame


# pylint: disable=unused-argument
@pytest.mark.xfail
@pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-8562")
def test_search_backend(login, navigator, request, custom_ui_backend):
    """
    Preparation:
        - Create custom backend
    Test if:
        - you search backend by name it will return the correct one
        - you search backend by system name it will return the correct one
    """
    name = blame(request, "name")
    sys_name = blame(request, "system")
    custom_ui_backend(name, sys_name)
    backends = navigator.navigate(BackendsView)

    for key in [name, sys_name]:
        backends.search(key)
        assert backends.table.row()[0].text == name
        assert backends.table.row()[1].text == sys_name


# pylint: disable=unused-argument
def test_search_multiple_backends(login, navigator, custom_backend, request):
    """
    Preparation:
        - Create 4 custom backends
    Test if:
        - you search backend by base name it will return the correct ones (first 3)
        - you search backend by specific name it will return the correct one
    """
    name = blame(request, "backend")
    params = [f"{name}_name", f"{name}_name2", f"{name}", blame(request, "RedHat")]
    for param in params:
        custom_backend(name=param, blame_name=False)

    backends = navigator.navigate(BackendsView)
    backends.search(name)

    assert len(list(backends.table.rows())) == 3

    backends.search(f"{name}_name2")
    assert backends.table.row()[0].text == f"{name}_name2"


def test_search_non_existing_value(request, login, navigator, custom_backend):
    """
    Preparation:
        - Create custom backend
    Test if:
        - you search backend by non-existing-value it won't return anything
    """
    custom_backend(name=blame(request, "name"))

    backends = navigator.navigate(BackendsView)
    backends.search("non-existing-value")

    assert len(list(backends.table.rows())) == 0
