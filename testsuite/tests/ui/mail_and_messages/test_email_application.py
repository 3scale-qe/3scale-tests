"""Test of automatic mails functionality connected to applications in UI"""
import pytest

from threescale_api.resources import Service
from testsuite.ui.views.admin.audience.application import ApplicationDetailView

pytestmark = pytest.mark.usefixtures("login")


@pytest.fixture(scope="module")
def service_settings(service_settings):
    """Set auth mode to app_id/app_key"""
    service_settings.update({"backend_version": Service.AUTH_APP_ID_KEY})
    return service_settings


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
    key = application.keys.list()["keys"][0]["key"]["value"]
    app.delete_app_key(key)

    mailhog_client.assert_message_received(
        subject="Application key has been deleted",
        content=f"A key has been deleted from your application {application['name']}.",
        expected_count=1,
    )
