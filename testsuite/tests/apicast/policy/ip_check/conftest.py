"ip_check conftest"
import pytest
from netifaces import interfaces, ifaddresses, AF_INET  # pylint: disable = no-name-in-module


@pytest.fixture(scope="module")
def ip4_addresses():
    "Get computer ip addresses"
    ip_list = []
    for interface in interfaces():
        interface = ifaddresses(interface)
        if AF_INET in interface:
            for link in interface[AF_INET]:
                ip_list.append(link['addr'])
    return ip_list
