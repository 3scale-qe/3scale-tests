"""
Conftest for mail and messages tests.

These tests require email notifications to be enabled.
"""

import pytest

NOTIFICATIONS = [
    "cinstance_plan_changed",
]


@pytest.fixture(scope="session", autouse=True)
def enable_notifications(threescale):
    """
    Enable notification preferences for notification-based UI testing.

    After porta PR #4039, notifications use a per-user NotificationPreferences model
    instead of account-level settings. In fresh deployments, notifications default to disabled.
    """
    params = {f"notification_preferences[{n}]": "true" for n in NOTIFICATIONS}
    threescale.rest.patch(path="/admin/api/personal/notification_preferences", data=params)
    # Enable service_plans_ui_visible which defaults to false, gating service_contract_created
    threescale.rest.put(path="/admin/api/settings", data={"service_plans_ui_visible": "true"})

    yield
