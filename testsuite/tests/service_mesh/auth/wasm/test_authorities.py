"""Tests wasm authorities filtering"""
from urllib.parse import urlsplit
from typing import List
import pytest
from testsuite.capabilities import Capability
from testsuite.gateways.wasm import ServiceMeshHttpClient


pytestmark = pytest.mark.required_capabilities(Capability.SERVICE_MESH_WASM)


@pytest.fixture(scope="module")
def client_ingress(api_client, extension) -> ServiceMeshHttpClient:
    """Returns api client using default ingress_url as ingress to service mesh."""
    client: ServiceMeshHttpClient = api_client()
    client.root_url = extension.ingress_url  # redundant, as its default, but included for better readability
    return client


@pytest.fixture(scope="module")
def client_alias(api_client, extension) -> ServiceMeshHttpClient:
    """Returns api client using first alias url as ingress to service mesh."""
    client: ServiceMeshHttpClient = api_client()
    client.root_url = extension.ingress_alias_url
    return client


def test_alias(extension, client_ingress, client_alias):
    """This test sets extension authorities to only accept alias host."""
    extension.replace_authorities([urlsplit(extension.ingress_alias_url).netloc])

    assert client_ingress.get("/").status_code == 403
    assert client_alias.get("/").status_code == 200


def test_both(extension, client_ingress, client_alias):
    """This test sets extension authorities to accept both alias and ingress host."""
    extension.replace_authorities(
        [urlsplit(extension.ingress_alias_url).netloc, urlsplit(extension.ingress_url).netloc])
    assert client_ingress.get("/").status_code == 200
    assert client_alias.get("/").status_code == 200


def test_empty(extension, client_ingress, client_alias):
    """This test sets empty extension authorities so no client should succeed."""
    extension.replace_authorities([])

    assert client_ingress.get("/").status_code == 403
    assert client_alias.get("/").status_code == 403


def test_glob_question_mark(extension, client_ingress, client_alias):
    """
    This test checks glob functionality in authorities string.
    Test sets url with replaced '.' character with '?' that denotes _any just one_
    Only authority host is the edited one.
    """
    url: str = urlsplit(extension.ingress_url).netloc
    url = url.replace(".", "?")

    extension.replace_authorities([url])
    assert client_ingress.get("/").status_code == 200
    assert client_alias.get("/").status_code == 403


@pytest.mark.parametrize("glob", ["*", "?+"])
def test_glob_star_plus(extension, client_ingress, client_alias, glob):
    """
    This test checks glob functionality in authorities string.
    First test checks that clients connect when last subdomain is changed to '*'
    Second test checks the same with '?+' that is equivalent to '*'
    Only authority host is the edited one.
    """
    url: List[str] = urlsplit(extension.ingress_url).netloc.split(".")
    url[0] = glob

    extension.replace_authorities([".".join(url)])
    assert client_ingress.get("/").status_code == 200
    assert client_alias.get("/").status_code == 200
