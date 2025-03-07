"""Conftest for"""

import base64
from contextlib import ExitStack
import pytest
import backoff

from testsuite import rawobj
from testsuite.capabilities import Capability
from testsuite.gateways.apicast.operator import OperatorApicast
from testsuite.gateways.apicast.system import SystemApicast
from testsuite.utils import blame, custom_policy

SCALE_OPERATOR = "3scale operator"
APICAST_OPERATOR = "APIcast operator"


@pytest.fixture(
    scope="module",
    params=[
        pytest.param(SystemApicast, marks=pytest.mark.disruptive, id=SCALE_OPERATOR),
        pytest.param(
            OperatorApicast,
            marks=pytest.mark.required_capabilities(Capability.CUSTOM_ENVIRONMENT),
            id=APICAST_OPERATOR,
        ),
    ],
)
def gateway_kind(request):
    """Gateway class to use for tests"""
    # pylint: disable=protected-access
    request.param.id = request._pyfuncitem.callspec.id
    return request.param


@pytest.fixture(scope="module")
def policy_settings():
    """return the example policy configuration"""
    return rawobj.PolicyConfig("example", configuration={}, version="0.1")


@pytest.fixture(scope="module")
def policy_secret(request, staging_gateway, gateway_kind):
    """
    Create an openshift secrets to use as custom policy based on https://github.com/3scale-qe/apicast-example-policy
    """
    name = blame(request, "secret")[-6:]  # 63 characters limit for referencing secret
    secrets = staging_gateway.openshift.secrets
    labels = {}
    if gateway_kind.id == SCALE_OPERATOR:
        labels = {"apimanager.apps.3scale.net/watched-by": "apimanager"}
    else:
        labels = {"apicast.apps.3scale.net/watched-by": "apicast"}
    secrets.create(name=name, string_data=custom_policy(), labels=labels)
    yield name
    del secrets[name]


@pytest.fixture(scope="module")
def changed_secret(staging_gateway, policy_secret):
    """
    Change secret with policy to check, if operator reconciles it.
    """
    # pylint: disable=protected-access
    generation = staging_gateway.deployment.get_generation()
    secrets = staging_gateway.openshift.secrets
    secret = secrets[policy_secret]
    example = base64.b64decode(secret._data["example.lua"].encode("ascii")).decode("ascii")
    example = example.replace("X-Example-Policy-Response", "X-Example-Example-Policy-Response")

    secrets.do_action("set", ["data", "secret/" + policy_secret, f"--from-literal=example.lua={example}"])
    staging_gateway.deployment.wait_for()
    staging_gateway.reload()
    staging_gateway.deployment.wait_for()

    def pods_ready(pods):
        pod_objects = pods.objects()
        status = bool(pod_objects)
        for pod in pod_objects:
            pod.refresh()
            obj_status = pod.model.status.conditions
            status = status and all(st["status"] == "True" for st in obj_status)
        return status

    wait_until = backoff.on_predicate(backoff.fibo, max_tries=30)
    with ExitStack() as stack:
        staging_gateway.openshift.prepare_context(stack)
        pods = staging_gateway.deployment.get_pods()
        wait_until(lambda: pods_ready(pods))

    assert staging_gateway.deployment.get_generation() > generation

    return secret


@pytest.fixture(scope="module")
def patch(staging_gateway, policy_secret):
    """Patch CRs"""
    staging_gateway.set_custom_policy({"name": "example", "version": "0.1", "secretRef": {"name": policy_secret}})
    yield
    staging_gateway.remove_custom_policy()
