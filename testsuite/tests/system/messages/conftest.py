"""
Conftest for messages tests.

These tests require email notifications to be enabled.
"""

import pytest

NOTIFICATIONS = [
    "account_created",
    "application_created",
    "service_contract_created",
    "account_deleted",
    "service_deleted",
]


@pytest.fixture(scope="session", autouse=True)
def enable_notifications(threescale):
    """
    Enable notification preferences for the current provider's admin user.

    After porta PR #4039, notifications use a per-user NotificationPreferences model
    instead of account-level settings. In fresh deployments, notifications default to disabled.
    """
    params = {f"notification_preferences[{n}]": "true" for n in NOTIFICATIONS}
    threescale.rest.patch(path="/admin/api/personal/notification_preferences", data=params)
    threescale.rest.put(path="/admin/api/settings", data={"service_plans_ui_visible": "true"})

    yield
