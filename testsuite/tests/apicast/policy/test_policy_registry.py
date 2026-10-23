"""
Rewrite spec/functional_specs/policies/policy_registry_spec.rb

Test if we are able to create custom policies through registers and use them.
"""

import pytest

from testsuite import rawobj
from testsuite.capabilities import Capability


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


@pytest.fixture
def custom_policies(threescale, schema, request, testconfig):
    """Create custom policies"""
    policies = []

    params1 = {"name": "policy_registry", "version": "0.1", "schema": schema}
    policy = threescale.policy_registry.create(params=params1)
    policies.append(policy)
    params2 = {"name": "policy_to_update", "version": "0.1", "schema": schema}
    policy = threescale.policy_registry.create(params=params2)
    policies.append(policy)

    if not testconfig["skip_cleanup"]:

        def _cleanup():
            for policy in policies:
                policy.delete()

        if not testconfig["skip_cleanup"]:
            request.addfinalizer(_cleanup)


@pytest.fixture(scope="module")
def policy_settings():
    """Add policy_registry policy with custom configuration"""
    return rawobj.PolicyConfig(
        "policy_registry",
        {
            "property1": {
                "value1": {"type": "string", "description": "Value1"},
                "value2": {"type": "string", "description": "Value2"},
            }
        },
    )


# pylint: disable=unused-argument
@pytest.mark.disruptive
@pytest.mark.required_capabilities(Capability.PRODUCTION_GATEWAY)
def test_policy_registry(custom_policies, threescale, schema, service, prod_client):
    """
    Test policy registry with custom policy
    Test if:
        - custom policies are in policy registry list
        - custom policies in registry policy list are registered correctly
        - custom policy is in service policy chain
        - we are able to get custom policy by ID
        - we are able to update custom policy
    """
    # Test if custom policies are in policy registry list
    policies = [r for r in threescale.policy_registry.list() if r["name"] in ("policy_registry", "policy_to_update")]

    assert len(policies) == 2

    # Test if custom policies in registry policy list are registered correctly
    assert policies[0]["name"] == "policy_registry"
    assert policies[0]["version"] == "0.1"
    assert policies[0]["schema"] == schema
    assert policies[1]["name"] == "policy_to_update"
    assert policies[1]["version"] == "0.1"
    assert policies[1]["schema"] == schema

    # Test if custom policy is in service policy chain
    policy = service.proxy.list()["policies_config"][1]

    assert policy["name"] == "policy_registry"
    assert prod_client().get("/get").status_code == 200

    # Test if we are able to get custom policy by ID
    policy = threescale.policy_registry.read(policies[1].entity_id)

    assert policy["name"] == "policy_to_update"
    assert policy["version"] == "0.1"
    assert policy["schema"] == schema

    # Test if we are able to update custom policy
    before_update = service.proxy.list()["policies_config"][1]["configuration"]
    schema["version"] = "0.2"
    params = {"name": "policy_to_update_updated", "version": "0.2", "schema": schema}
    threescale.policy_registry.update(policies[1].entity_id, params=params)
    policy = threescale.policy_registry.read(policies[1].entity_id)
    after_update = service.proxy.list()["policies_config"][1]["configuration"]

    assert policy["name"] == "policy_to_update_updated"
    assert policy["version"] == "0.2"
    assert policy["schema"] == schema
    assert before_update == after_update
