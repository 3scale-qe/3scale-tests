"""Conftest for """
import pytest

from testsuite import rawobj
from testsuite.capabilities import Capability
from testsuite.gateways.apicast.operator import OperatorApicast
from testsuite.gateways.apicast.system import SystemApicast
from testsuite.utils import blame, custom_policy


@pytest.fixture(scope="module", params=[
    pytest.param(SystemApicast, marks=pytest.mark.disruptive, id="3scale operator"),
    pytest.param(OperatorApicast, marks=pytest.mark.required_capabilities(Capability.CUSTOM_ENVIRONMENT),
                 id="APIcast operator")
])
def gateway_kind(request):
    """Gateway class to use for tests"""
    return request.param


@pytest.fixture(scope="module")
def policy_settings():
    """return the example policy configuration"""
    return rawobj.PolicyConfig("example", configuration={}, version="0.1")


@pytest.fixture(scope="module")
def policy_secret(request, staging_gateway):
    """
    Create an openshift secrets to use as custom policy based on https://github.com/3scale-qe/apicast-example-policy
    """
    name = blame(request, "secret")
    secrets = staging_gateway.openshift.secrets
    secrets.create(name=name, string_data=custom_policy())
    yield name
    del secrets[name]


@pytest.fixture(scope="module")
def patch(staging_gateway, policy_secret):
    """Patch CRs"""
    staging_gateway.set_custom_policy({"name": "example", "version": "0.1", "secretRef": {"name": policy_secret}})
    yield
    staging_gateway.remove_custom_policy()
