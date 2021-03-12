"""
Rewrite spec/ui_specs/webhooks/webhooks_keys_spec.rb
"""

import xml.etree.ElementTree as Et

import pytest
from threescale_api.resources import Service

from testsuite.ui.views.admin import WebhooksView
from testsuite.ui.views.admin.audience.application import ApplicationDetailView


# pylint: disable=too-many-arguments, disable=unused-argument
@pytest.fixture(scope="module", autouse=True)
def setup(browser, navigator, login, requestbin, request, threescale):
    """
    Configure webhooks and create requestbin.
    :return: name of specific requestbin
    """
    webhooks = navigator.navigate(WebhooksView)
    webhooks.webhook_check("Keys", requestbin.url)
    request.addfinalizer(threescale.webhooks.clear)


def test_user_key_create_delete(login, service, application, requestbin, navigator):
    """
    Test:
        - Change service auth to application key
        - Create application key
        - Get webhook response for key_created
        - Assert that webhook response is not None
        - Create application key
        - Delete application key
        - Get webhook response for key_deleted
        - Assert that webhook response is not None
    """
    service.update({"backend_version": Service.AUTH_APP_ID_KEY})
    service.proxy.list().update()
    app = navigator.navigate(ApplicationDetailView, application_id=application.entity_id)

    # Create user key
    app.add_random_app_key()
    webhook = requestbin.get_webhook("key_created", str(application.entity_id))
    assert webhook is not None

    # Delete user key
    app.add_random_app_key()  # Application has to contains at least 2 keys to be able to delete one through UI
    key = application.keys.list()["keys"][0]["key"]["value"]
    app.delete_app_key(key)
    webhook = requestbin.get_webhook("key_deleted", str(application.entity_id))
    assert webhook is not None


def test_user_key_regenerate(login, service, application, account, requestbin, navigator):
    """
    Test:
        - Change service auth to user key
        - Regenerate user key
        - Get webhook response for application_key_updated
        - Assert that webhook response is not None
        - Assert that response xml body contains right name
        - Assert that response xml body contains right user_key
    """
    service.update({"backend_version": Service.AUTH_USER_KEY})
    service.proxy.list().update()

    app = navigator.navigate(ApplicationDetailView, application_id=application.entity_id)
    app.regenerate_user_key()
    application = account.applications.read_by_name(application.entity_name)

    webhook = requestbin.get_webhook("key_updated", str(application.entity_id))
    assert webhook is not None

    xml = Et.fromstring(webhook)
    name = xml.find(".//application/name").text
    user_key = xml.find(".//user_key").text
    assert name == application["name"]
    assert user_key == application["user_key"]
