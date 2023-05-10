"""
Rewrite spec/ui_specs/webhooks/webhooks_applications_spec.rb
"""

import xml.etree.ElementTree as Et

import pytest

from testsuite import rawobj, resilient
from testsuite.ui.views.admin.audience.application import ApplicationEditView, ApplicationDetailView
from testsuite.ui.views.admin.settings.webhooks import WebhooksView
from testsuite.utils import blame

pytestmark = pytest.mark.usefixtures("login")


@pytest.fixture(scope="module", autouse=True)
def setup(navigator, custom_admin_login, requestbin, request, threescale):
    """
    Configure webhooks and create requestbin.
    :return: name of specific requestbin
    """
    custom_admin_login()
    webhooks = navigator.navigate(WebhooksView)
    webhooks.webhook_check("Applications", requestbin.url)
    request.addfinalizer(threescale.webhooks.clear)


@pytest.fixture(scope="module")
def custom_app(service, custom_app_plan, custom_application, lifecycle_hooks, request):
    """
    Create an application
    """

    def _custom_app(autoclean=True):
        plan = custom_app_plan(rawobj.ApplicationPlan(blame(request, "app_plan")), service)
        return custom_application(
            rawobj.Application(blame(request, "app_name"), plan), autoclean=autoclean, hooks=lifecycle_hooks
        )

    return _custom_app


def test_application_created(requestbin, ui_application):
    """
    Test:
        - Create application
        - Get webhook response for created
        - Assert that webhook response is not None
        - Assert that response xml body contains right account id
    """
    webhook = requestbin.get_webhook("created", str(ui_application.entity_id))
    assert webhook is not None

    xml = Et.fromstring(webhook)
    acc_id = xml.find(".//user_account_id").text
    assert acc_id == str(ui_application.parent.entity_id)


def test_application_updated(custom_app, navigator, requestbin, service):
    """
    Test:
        - Update application
        - Get webhook response for updated
        - Assert that webhook response is not None
        - Assert that response xml body contains right application name and description
    """
    application = custom_app()
    app = navigator.navigate(ApplicationEditView, application=application, product=service)
    app.update("updated_name", "updated_description")
    webhook = requestbin.get_webhook("updated", str(application.entity_id))
    assert webhook is not None

    xml = Et.fromstring(webhook)
    name = xml.find(".//application/name").text
    decs = xml.find(".//description").text
    assert name == "updated_name"
    assert decs == "updated_description"


def test_application_suspended(custom_app, navigator, requestbin, service):
    """
    Test:
        - Suspend application
        - Get webhook response for suspended
        - Assert that webhook response is not None
        - Assert that response xml body contains right application state
    """

    application = custom_app()
    app = navigator.navigate(ApplicationDetailView, application=application, product=service)
    app.suspend()
    webhook = requestbin.get_webhook("suspended", str(application.entity_id))
    assert webhook is not None

    xml = Et.fromstring(webhook)
    state = xml.find(".//application/state").text
    assert state == "suspended"


# pylint: disable=too-many-arguments, too-many-locals,
def test_application_plan_changed(custom_app_plan, request, navigator, service, custom_app, requestbin):
    """
    Test:
        - Change application plan
        - Get webhook response for plan_changed
        - Assert that webhook response is not None
        - Assert that response xml body contains right application name, plan id and plan name
    """
    application = custom_app()
    app_plan = custom_app_plan(rawobj.ApplicationPlan(blame(request, "app_plan")), service)
    app = navigator.navigate(ApplicationDetailView, application=application, product=service)
    app.change_plan(app_plan["name"])

    webhook = requestbin.get_webhook("plan_changed", str(application.entity_id))
    assert webhook is not None

    xml = Et.fromstring(webhook)
    name = xml.find(".//application/name").text
    plan_id = xml.find(".//plan//id").text
    plan_name = xml.find(".//plan//name").text
    assert name == application["name"]
    assert plan_id == str(app_plan.entity_id)
    assert plan_name == app_plan["name"]


def test_user_key_updated(custom_app, navigator, requestbin, account, service):
    """
    Test:
        - Create custom application
        - Regenerate user key of that application
        - Get webhook response for user_key_updated
        - Assert that webhook response is not None
        - Assert that response xml body contains right application name and user_key
    """
    application = custom_app()
    app = navigator.navigate(ApplicationDetailView, application=application, product=service)
    app.regenerate_user_key()
    application = resilient.resource_read_by_name(account.applications, application.entity_name)

    webhook = requestbin.get_webhook("user_key_updated", str(application.entity_id))
    assert webhook is not None

    xml = Et.fromstring(webhook)
    name = xml.find(".//application/name").text
    user_key = xml.find(".//user_key").text
    assert name == application["name"]
    assert user_key == application["user_key"]


def test_application_deleted(custom_app, navigator, requestbin, service):
    """
    Test:
        - Create application
        - Get webhook response for created
        - Assert that webhook response is not None
        - Assert that response xml body contains right account id
    """
    application = custom_app(autoclean=False)
    app = navigator.navigate(ApplicationEditView, application=application, product=service)
    app.delete()
    webhook = requestbin.get_webhook("deleted", str(application.entity_id))
    assert webhook is not None
