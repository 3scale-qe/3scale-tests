"""
    rewrite of admin dashboard test to master (testing the master dashboard)

    Tests in this file are testing the functionality of the master dashboard.
"""
from testsuite.ui.views.master.foundation import MasterDashboardView


# pylint: disable=unused-argument
def test_dashboard_is_loaded_correctly(master_login, navigator):
    """
    Test:
        - Navigates to Dashboard
        - Checks whether everything is on the dashboard that is supposed to be there
    """
    dashboard = navigator.navigate(MasterDashboardView)

    assert dashboard.is_displayed
