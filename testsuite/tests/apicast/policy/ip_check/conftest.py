"""ip_check conftest"""
import pytest
import requests


@pytest.fixture(scope="module")
def ip4_addresses(private_base_url):
    """
    Get computer ip addresses
    A request is sent to httpbin to determine the real ip addresses
    for container based deplyoment
    """

    response = requests.get(private_base_url("httpbin_nossl").rstrip("/") + "/ip")

    return response.json()["origin"].split(",")
