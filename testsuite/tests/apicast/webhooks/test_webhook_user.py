"""
Based on spec/ui_specs/webhooks/webhooks_users_spec.rb (ruby test is via UI)
"""

import xml.etree.ElementTree as Et


import pytest

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
    threescale.webhooks.setup("Users", requestbin.url)
    request.addfinalizer(threescale.webhooks.clear)


def test_user(account, request, requestbin):
    """
    Test:
        - Create user
        - Get webhook response for created
        - Assert that webhook response is not None
        - Assert that response xml body contains right username
        - Update user
        - Get webhook response for updated
        - Assert that webhook response is not None
        - Assert that response xml body contains right username
        - Delete user
        - Get webhook response for deleted
        - Assert that webhook response is not None
    """
    # Crete user
    email = blame(request, "test")
    user = account.users.create({"username": blame(request, "user"), "email": f"{email}@example.com"})
    webhook = requestbin.get_webhook("created", str(user.entity_id))
    assert webhook is not None

    xml = Et.fromstring(webhook)
    username = xml.find(".//username").text
    assert username == user.entity_name

    # Update user
    user.update({"username": "updated_username"})
    webhook = requestbin.get_webhook("updated", str(user.entity_id))
    assert webhook is not None

    xml = Et.fromstring(webhook)
    username = xml.find(".//username").text
    assert username == user.entity_name

    # Delete user
    user.delete()
    webhook = requestbin.get_webhook("deleted", str(user.entity_id))
    assert webhook is not None
