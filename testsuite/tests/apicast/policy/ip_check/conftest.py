"""ip_check conftest"""
import pytest
import requests

from netifaces import interfaces, ifaddresses, AF_INET  # pylint: disable = no-name-in-module

from testsuite.echoed_request import EchoedRequest


@pytest.fixture(scope="module")
def ip4_addresses(private_base_url):
    """
    Get computer ip addresses
    A request is sent to httpbin to determine the real ip addresses
    for container based deplyoment
    """
    response = requests.get(private_base_url('httpbin') + '/anything',
                            verify=False)

    echoed_request = EchoedRequest.create(response)
    ip_list = set(echoed_request.json['origin'].split(','))
    for interface in interfaces():
        interface = ifaddresses(interface)
        if AF_INET in interface:
            for link in interface[AF_INET]:
                ip_list.add(link['addr'])
    return list(ip_list)
