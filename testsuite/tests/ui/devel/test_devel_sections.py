"""Test for developer portal sections"""

import pytest
from packaging.version import Version

from testsuite import TESTED_VERSION
from testsuite.ui.views.admin.audience.account import AccountUserGroupView
from testsuite.ui.views.admin.audience.developer_portal import (
    CMSEditPageView,
    CMSNewPageView,
    CMSNewSectionView,
    DeveloperPortalGroupNewView,
    DeveloperPortalGroupView,
)
from testsuite.ui.views.common.foundation import NotFoundView
from testsuite.utils import blame


@pytest.fixture(scope="module")
def dev_portal_section(navigator, request, threescale):
    """Creates a new section in developer portal"""
    view = navigator.navigate(CMSNewSectionView)
    section_name = blame(request, "TestSection")
    section_path = blame(request, "section")
    view.create(section_name, section_path, False)
    section_id = navigator.browser.url.split("/")[-2]

    request.addfinalizer(lambda: threescale.cms_sections.delete(section_id))

    return section_name


@pytest.fixture(scope="module")
def dev_portal_page(navigator, request, dev_portal_section, threescale):
    """Creates a new page in developer portal and assign it to section"""
    view = navigator.navigate(CMSNewPageView)
    page_name = blame(request, "TestPage")
    page_path = blame(request, "/test")

    view.create(page_name, "|— " + dev_portal_section, page_path, "<h1>Test</h1>")
    page_id = navigator.browser.url.split("/")[-2]

    request.addfinalizer(lambda: threescale.cms_pages.delete(page_id))

    view = navigator.new_page(CMSEditPageView, page_id=page_id)
    view.publish()

    return view.get_path()


@pytest.fixture(scope="module")
def dev_portal_group(navigator, request, account, dev_portal_section, custom_admin_login):
    """Creates a new group in developer portal and assign account to this group"""
    custom_admin_login()
    group_name = blame(request, "TestGroup")
    view = navigator.navigate(DeveloperPortalGroupNewView)

    def cleanup():
        custom_admin_login()
        view = navigator.navigate(DeveloperPortalGroupView)
        view.delete_group(group_name)

    request.addfinalizer(cleanup)
    view.create(group_name, [dev_portal_section])

    view = navigator.navigate(AccountUserGroupView, account=account)
    view.update([group_name])


@pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-9020")
@pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-836")
@pytest.mark.skipif(TESTED_VERSION < Version("2.14-dev"), reason="TESTED_VERSION < Version('2.14-dev')")
@pytest.mark.usefixtures("dev_portal_group")
@pytest.mark.usefixtures("login")
def test_dev_portal_sections(account, custom_devel_login, browser, testconfig, dev_portal_page):
    """
    Preparation:
        - Creates a new dev portal section
        - Creates a new dev portal page in that section
        - Creates a new dev portal group for that section
    Test:
        - Login to dev portal as account with assigned group
        - Assert that this account has access to this page
        - Login to dev portal as account without group
        - Assert that this account hasn't access to this page
    """
    custom_devel_login(account=account)
    browser.url = testconfig["threescale"]["devel"]["url"] + dev_portal_page

    assert browser.element(".//h1").accessible_name == "Test"

    custom_devel_login(name="john", password="123456", fresh=True)
    browser.url = testconfig["threescale"]["devel"]["url"] + dev_portal_page

    assert NotFoundView(browser).is_displayed
