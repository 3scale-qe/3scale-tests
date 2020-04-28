"Toolbox conftest"

import pytest

from dynaconf import settings
from threescale_api import client


@pytest.fixture(scope="module")
def dest_client():
    """ Returns threescale client to destination instance """
    return client.ThreeScaleClient(
        settings['toolbox']['destination_endpoint'],
        settings['toolbox']['destination_provider_key'],
        ssl_verify=settings['ssl_verify'])
