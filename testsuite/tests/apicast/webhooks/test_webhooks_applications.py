"""
Based on spec/ui_specs/webhooks/webhooks_applications_spec.rb (ruby test is via UI)
"""

import xml.etree.ElementTree as Et


import pytest

from testsuite import rawobj
from testsuite.utils import blame

# webhook tests seem disruptive to requestbin as they reset it with no mercy
pytestmark = [
    pytest.mark.require_version("2.8.3"),
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-5207"),
    pytest.mark.disruptive]


@pytest.fixture(scope="module", autouse=True)
def setup(requestbin, request, threescale):
    """
    Configure webhooks and create requestbin.
    :return: name of specific requestbin
    """
    threescale.webhooks.setup("Applications", requestbin.url)
    request.addfinalizer(threescale.webhooks.clear)


@pytest.fixture(scope="module")
def custom_app(custom_application, custom_app_plan, service, lifecycle_hooks, request):
    """
    Create a second application
    """
    plan = custom_app_plan(rawobj.ApplicationPlan(blame(request, "app_plan")), service)
    return custom_application(rawobj.Application(blame(request, "app_name"), plan), autoclean=False,
                              hooks=lifecycle_hooks)


def test_application_created(application, requestbin):
    """
    Test:
        - Create application
        - Get webhook response for created
        - Assert that webhook response is not None
        - Assert that response xml body contains right account id
    """

    webhook = requestbin.get_webhook("created", str(application.entity_id))
    assert webhook is not None

    xml = Et.fromstring(webhook)
    acc_id = xml.find(".//user_account_id").text
    assert acc_id == str(application.parent.entity_id)


def test_application_updated(application, requestbin):
    """
    Test:
        - Update application
        - Get webhook response for updated
        - Assert that webhook response is not None
        - Assert that response xml body contains right application name and description
      """

    application.update({"name": "updated_name", "description": 'updated_description'})
    webhook = requestbin.get_webhook("updated", str(application.entity_id))
    assert webhook is not None

    xml = Et.fromstring(webhook)
    name = xml.find(".//application/name").text
    decs = xml.find(".//description").text
    assert name == "updated_name"
    assert decs == "updated_description"


def test_application_suspended(account, application, requestbin):
    """
    Test:
        - Suspend application
        - Get webhook response for suspended
        - Assert that webhook response is not None
        - Assert that response xml body contains right application state
    """

    account.applications.suspend(application.entity_id)
    webhook = requestbin.get_webhook("suspended", str(application.entity_id))
    assert webhook is not None

    xml = Et.fromstring(webhook)
    state = xml.find(".//application/state").text
    assert state == "suspended"


# pylint: disable=too-many-arguments
def test_application_plan_changed(application, custom_app_plan, request, service, account, requestbin):
    """
    Test:
        - Change application plan
        - Get webhook response for plan_changed
        - Assert that webhook response is not None
        - Assert that response xml body contains right application name, plan id and plan name
    """

    app_plan = custom_app_plan(rawobj.ApplicationPlan(blame(request, "app_plan")), service)
    account.applications.change_plan(application.entity_id, app_plan.entity_id)
    webhook = requestbin.get_webhook("plan_changed", str(application.entity_id))
    assert webhook is not None

    xml = Et.fromstring(webhook)
    name = xml.find(".//application/name").text
    plan_id = xml.find(".//plan//id").text
    plan_name = xml.find(".//plan//name").text
    assert name == application.entity["name"]
    assert plan_id == str(app_plan.entity_id)
    assert plan_name == app_plan.entity["name"]


def test_user_key_updated():
    """
    Test if webhook response for user key updated
    """

    # TODO - Missing API endpoint
    # https://issues.redhat.com/browse/THREESCALE-5347


def test_application_deleted(custom_app, requestbin):
    """
    Test:
        - Create application
        - Get webhook response for created
        - Assert that webhook response is not None
        - Assert that response xml body contains right account id
    """

    custom_app.delete()
    webhook = requestbin.get_webhook("deleted", str(custom_app.entity_id))
    assert webhook is not None
