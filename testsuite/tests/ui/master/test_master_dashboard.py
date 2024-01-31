"""
    rewrite of admin dashboard test to master (testing the master dashboard)

    Tests in this file are testing the functionality of the master dashboard.
"""

import pytest

from testsuite.ui.views.master.foundation import MasterDashboardView


@pytest.mark.usefixtures("master_login")
def test_dashboard_is_loaded_correctly(navigator):
    """
    Test:
        - Navigates to Dashboard
        - Checks whether everything is on the dashboard that is supposed to be there
    """
    dashboard = navigator.navigate(MasterDashboardView)

    assert dashboard.is_displayed
