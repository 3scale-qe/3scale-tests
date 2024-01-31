"""Tokens conftest"""

from urllib.parse import urljoin

import pytest
import requests
from threescale_api.resources import InvoiceState


@pytest.fixture(scope="module")
def api_client(testconfig):
    """
    New and different 3scale api client is needed because the one we regularly use
    needs token upon creation and use this token with every api request.
    The tests that use this client required that bunch of requests are made with different custom tokens.
    """

    def _api_client(method, path, token, params=None, headers=None, **kwargs):
        url = urljoin(testconfig["threescale"]["admin"]["url"], path)
        url = url + ".json"
        headers = headers or {}
        params = params or {}
        params.update(access_token=token)
        return requests.request(
            method=method, url=url, headers=headers, params=params, verify=testconfig["ssl_verify"], **kwargs
        )

    return _api_client


@pytest.fixture
def invoice(threescale, account):
    """Crate invoice through API"""
    invoice = threescale.invoices.create({"account_id": account["id"]})

    yield invoice

    invoice.state_update(InvoiceState.CANCELLED)


@pytest.fixture(
    scope="module", params=[pytest.param((False, 403), id="Read Only"), pytest.param((True, 201), id="Read and Write")]
)
def permission(request):
    """Permission of token"""
    return request.param


@pytest.fixture
def schema():
    """
    :return: Schema of custom policy
    """
    return {
        "$schema": "http://apicast.io/policy-v1/schema#manifest#",
        "name": "APIcast Example Policy",
        "summary": "This is just an example.",
        "description": "This policy is just an example how to write your custom policy.",
        "version": "0.1",
        "configuration": {
            "type": "object",
            "properties": {
                "property1": {
                    "type": "array",
                    "description": "list of properties1",
                    "items": {
                        "type": "object",
                        "properties": {
                            "value1": {"type": "string", "description": "Value1"},
                            "value2": {"type": "string", "description": "Value2"},
                        },
                        "required": ["value1"],
                    },
                }
            },
        },
    }
