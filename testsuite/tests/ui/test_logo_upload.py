"""Tests developer portal logo upload"""

import pytest
import importlib_resources as resources

from testsuite.ui.views.admin.audience.developer_portal import DeveloperPortalLogoView
from testsuite.utils import warn_and_skip


@pytest.fixture(scope="module", autouse=True)
def skip_rhoam(testconfig):
    """Logo upload does not work on RHOAM for some reason"""
    if testconfig["threescale"]["deployment_type"] == "rhoam":
        warn_and_skip(skip_rhoam.__doc__)


@pytest.mark.sandbag  # doesn't work on RHOAM
@pytest.mark.parametrize("file_name", ["rh-3scale.png", "3scale_logo.png"])
@pytest.mark.usefixtures("login")
def test_logo_upload(navigator, file_name):
    """
    A test that checks if it possible to upload different types of logos (png, gif)
    - Upload logo
    - Assert that logo was uploaded
    - Delete logo
    - Assert that logo was deleted
    """
    logo_file = resources.files("testsuite.resources.logo").joinpath(file_name)
    logo_page = navigator.navigate(DeveloperPortalLogoView)
    logo_page.upload_logo(logo_file)

    assert logo_page.logo.is_displayed
    assert file_name in logo_page.logo.src
    assert logo_page.delete_logo_button.is_displayed

    logo_page.delete_logo_button.click()
    assert not logo_page.logo.is_displayed
    assert not logo_page.delete_logo_button.is_displayed
