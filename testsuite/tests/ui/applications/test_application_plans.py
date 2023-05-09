"""Tests of applications plans"""
import pytest
from packaging.version import Version  # noqa # pylint: disable=unused-import

from testsuite import TESTED_VERSION  # noqa # pylint: disable=unused-import
from testsuite import rawobj
from testsuite.ui.views.admin.product.application import ApplicationPlansView
from testsuite.utils import blame

pytestmark = pytest.mark.usefixtures("login")


def test_app_plan_create(custom_ui_app_plan, request, service):
    """
    Test:
        - create application plan via UI
        - assert that plan was created
    """
    name = blame(request, "app-plan")

    plan = custom_ui_app_plan(name, service)
    assert plan
    assert plan["name"] == name


@pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-825")
@pytest.mark.skipif("TESTED_VERSION < Version('2.13')")
def test_default_app_plan_change(request, service, custom_app_plan, navigator):
    """
    Test of default application plan change:
        - assert the change button is disabled
        - change the default application plan and assert if confirmation notice is received
        - assert the change button is disabled
        - change the plan on select, assert change button is available
        - go back to previous plan and confirm change button is disabled
    """
    plan1 = custom_app_plan(rawobj.ApplicationPlan(blame(request, "app-plan")), service)
    plan2 = custom_app_plan(rawobj.ApplicationPlan(blame(request, "app-plan")), service)
    app_plans_view = navigator.navigate(ApplicationPlansView, product=service)

    assert not app_plans_view.change_plan_button.is_enabled
    app_plans_view.default_plan_select.item_select(plan1["name"])
    assert app_plans_view.change_plan_button.is_enabled
    app_plans_view.change_plan_button.click()
    assert app_plans_view.notification.is_displayed
    assert app_plans_view.notification.string_in_flash_message("the default plan has been changed.")

    assert not app_plans_view.change_plan_button.is_enabled
    app_plans_view.default_plan_select.item_select(plan2["name"])
    assert app_plans_view.change_plan_button.is_enabled
    app_plans_view.default_plan_select.item_select(plan1["name"])
    assert not app_plans_view.change_plan_button.is_enabled


@pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-8979")
@pytest.mark.skipif("TESTED_VERSION < Version('2.13')")
def test_unset_default_app_plan(request, service, custom_app_plan, navigator):
    """
    Test unset default application plan:
        - change the default application plan and assert if confirmation notice is received
        - unset default plan
        - assert confirmation notice is received and application plans page is displayed
    """
    app_plan = custom_app_plan(rawobj.ApplicationPlan(blame(request, "app-plan")), service)
    app_plans_view = navigator.navigate(ApplicationPlansView, product=service)
    app_plans_view.change_default_plan(app_plan["name"])
    assert app_plans_view.notification.is_displayed
    assert app_plans_view.notification.string_in_flash_message("the default plan has been changed.")

    app_plans_view.change_default_plan("No plan selected")
    assert app_plans_view.notification.is_displayed
    assert app_plans_view.notification.string_in_flash_message("the default plan has been changed.")
    assert app_plans_view.is_displayed
