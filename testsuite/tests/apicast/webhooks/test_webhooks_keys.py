"""
Based on spec/ui_specs/webhooks/webhooks_keys_spec.rb (ruby test is via UI)
"""


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
    threescale.webhooks.setup("Keys", requestbin.url)
    request.addfinalizer(threescale.webhooks.clear)


def test_user_key(application, request, requestbin):
    """
    Test:
        - Create application key
        - Get webhook response for key_created
        - Assert that webhook response is not None
        - Delete application key
        - Get webhook response for key_deleted
        - Assert that webhook response is not None
    """
    # Create user key
    name = blame(request, "key")
    application.keys.create({"key": name})
    webhook = requestbin.get_webhook("key_created", str(application.entity_id))
    assert webhook is not None

    # Update user key

    # TODO - Missing API endpoint
    # https://issues.redhat.com/browse/THREESCALE-5347

    # Delete user key
    application.keys.delete(name)
    webhook = requestbin.get_webhook("key_deleted", str(application.entity_id))
    assert webhook is not None
