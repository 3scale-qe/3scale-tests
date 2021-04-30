"Toolbox conftest"

import backoff
import pytest

from threescale_api import client, errors

from testsuite import rawobj
from testsuite.config import settings
from testsuite.utils import blame


@pytest.fixture(scope="module")
def dest_client(custom_tenant, request) -> client.ThreeScaleClient:
    """ Returns threescale client to destination instance """
    if 'toolbox' in settings and 'destination_endpoint' in settings['toolbox']:
        destination_endpoint = settings['toolbox']['destination_endpoint']
        destination_provider = settings['toolbox']['destination_provider_key']
    else:
        tenant = custom_tenant()

        destination_endpoint = tenant.entity["signup"]["account"]["admin_base_url"]
        destination_provider = tenant.entity["signup"]["access_token"]["value"]

        unprivileged_client = client.ThreeScaleClient(destination_endpoint, destination_provider, ssl_verify=False)

        token_name = blame(request, "at")

        @backoff.on_exception(backoff.fibo(), errors.ApiClientError, max_time=8)
        def _wait_on_ready_tenant():
            unprivileged_client.services.list()

        _wait_on_ready_tenant()

        access_token = unprivileged_client.access_tokens.create(rawobj.AccessToken(
            token_name, "rw", ["finance", "account_management",
                               "stats", "policy_registry"]))

        destination_provider = access_token["value"]  # overriding with greater and better access key

    return client.ThreeScaleClient(destination_endpoint,
                                   destination_provider,
                                   ssl_verify=settings['ssl_verify'])


@pytest.fixture(scope="module")
def threescale_src1(threescale):
    """ Returns url for source tenant with access token with all rw rights """
    return threescale.url_with_token


@pytest.fixture(scope="module")
def threescale_dst1(dest_client):
    """ Returns url for destination tenant with access token with all rw rights """
    return dest_client.url_with_token
