"""Test of automatic mails functionality connected to applications in UI"""

import pytest
from threescale_api.resources import Service

from testsuite import rawobj
from testsuite.utils import blame

from testsuite.ui.views.admin.audience.application import ApplicationDetailView
from testsuite.ui.views.devel.applications import DevelApplicationDetailView

pytestmark = pytest.mark.usefixtures("login")


@pytest.fixture(scope="module")
def service_settings(service_settings):
    """Set auth mode to app_id/app_key"""
    service_settings.update({"backend_version": Service.AUTH_APP_ID_KEY})
    return service_settings


@pytest.fixture(scope="function")
def extra_plan(request, service, custom_app_plan):
    """Additional application plan to choose"""
    return custom_app_plan(rawobj.ApplicationPlan(blame(request, "extra_plan")), service)


@pytest.fixture(scope="module")
def app_id_key_service(application, service, navigator):
    """Product with APP ID +APP KEY authentication"""
    app = navigator.navigate(ApplicationDetailView, application=application, product=service)
    app.add_random_app_key()
    return service


# pylint: disable=unused-argument
def test_app_key_create_mails_notification(app_id_key_service, application, mailhog_client):
    """
    Test:
        - Assert that mail about creating new key was sent
    """
    mailhog_client.assert_message_received(
        subject="Application key has been created",
        content=f"A new key has been created for your application {application['name']}.",
        expected_count=1,
    )


def test_app_key_delete_mails_notification(app_id_key_service, application, navigator, mailhog_client):
    """
    Test:
        - Add second key to application (to delete app key there must be at least one left)
        - Assert that mail about deleting new key was sent
    """
    app = navigator.navigate(ApplicationDetailView, application=application, product=app_id_key_service)
    app.add_random_app_key()
    key = application.keys.list()[-1]["value"]
    app.delete_app_key(key)

    mailhog_client.assert_message_received(
        subject="Application key has been deleted",
        content=f"A key has been deleted from your application {application['name']}.",
        expected_count=1,
    )


def test_mail_application_plan_changed(navigator, service, application, extra_plan, mailhog_client):
    """
    Test:
        - Change application plan
        - Assert that API consumer is notified about plan change
        - Assert that API provider is notified about plan change
    """
    app = navigator.navigate(ApplicationDetailView, application=application, product=service)
    app.change_plan(extra_plan["name"])

    mailhog_client.assert_message_received(
        subject=f"Application plan changed to '{extra_plan['name']}'", expected_count=1
    )
    mailhog_client.assert_message_received(
        subject=f"Application {application.entity_name} has changed to plan {extra_plan['name']}", expected_count=1
    )


# pylint: disable=too-many-arguments
def test_mail_request_app_plan_changed(account, navigator, custom_devel_login, application, extra_plan, mailhog_client):
    """
    Test:
        - Request to change application plan
        - Assert that API consumer is notified about request plan change
        - Assert that API provider is notified about request plan change
    """
    custom_devel_login(account=account)
    app_view = navigator.navigate(DevelApplicationDetailView, application=application)
    app_view.change_plan_link.click()
    app_view.change_plan(extra_plan["id"])
    mailhog_client.assert_message_received(
        subject=f"Action required: {account.entity_name} from {account.entity_name} requested an app plan change",
        expected_count=1,
    )
    mailhog_client.assert_message_received(
        subject="Plan change request has been received",
        content=f"Dear {account.entity_name},\r\n\r\nProvider Name has received your request to have your plan "
        f"changed to {extra_plan['name']} for application {application.entity_name}.",
        expected_count=1,
    )
