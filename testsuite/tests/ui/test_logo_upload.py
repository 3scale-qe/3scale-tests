"""Tests developer portal logo upload"""

import pytest
import importlib_resources as resources

from testsuite.ui.views.admin.audience.developer_portal import DeveloperPortalLogoView


# pylint: disable=unused-argument
@pytest.mark.parametrize("file_name", ["rh-3scale.png", "3scale_logo.png", "rh-3scale-gif.gif"])
def test_logo_upload(login, navigator, file_name):
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
