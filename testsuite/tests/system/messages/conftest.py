"""Conftest for messages/email tests"""

import pytest
from testsuite.mailhog import MailhogClient


@pytest.fixture(scope="module")
def mailhog_client(openshift):
    """Creates mailhog client with url set to the
     route of the 'mailhog' app in the openshift"""
    return MailhogClient(openshift())
