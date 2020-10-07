"Toolbox conftest"

import pytest

from threescale_api import client
from testsuite.config import settings


@pytest.fixture(scope="module")
def dest_client():
    """ Returns threescale client to destination instance """
    return client.ThreeScaleClient(
        settings['toolbox']['destination_endpoint'],
        settings['toolbox']['destination_provider_key'],
        ssl_verify=settings['ssl_verify'])
