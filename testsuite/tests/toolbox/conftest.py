"Toolbox conftest"

import pytest

from threescale_api import client

from testsuite import rawobj
from testsuite.config import settings
from testsuite.utils import blame


# pylint: disable=unused-argument
@pytest.fixture(scope="session", autouse=True)
def fixed_order(custom_tenant, custom_account, custom_user):
    """Ensure proper order of initialization **AND** cleanup

    Order in initialization of session scoped fixtures in toolbox tests is
    somehow incorrect. That causes error during cleanup when fixtures are
    executed in wrong order. It doesn't seem to be easy to find particular
    order problems and for example custom_tenant fixture probably can't be
    fixed at all as it is included indirectly by module scoped fixture that may
    (or may not) cause that custom_tenant is initialized always too late (and
    cleaned too early).
    """


@pytest.fixture(scope="module")
def dest_client(custom_tenant, request) -> client.ThreeScaleClient:
    """Returns threescale client to destination instance"""
    if "toolbox" in settings and "destination_endpoint" in settings["toolbox"]:
        destination_endpoint = settings["toolbox"]["destination_endpoint"]
        destination_provider = settings["toolbox"]["destination_provider_key"]
    else:
        tenant = custom_tenant()

        destination_endpoint = tenant.admin_base_url

        unprivileged_client = tenant.admin_api(ssl_verify=False, wait=True)

        token_name = blame(request, "at")

        access_token = unprivileged_client.access_tokens.create(
            rawobj.AccessToken(token_name, "rw", ["finance", "account_management", "stats", "policy_registry"])
        )

        destination_provider = access_token["value"]  # overriding with greater and better access key

    return client.ThreeScaleClient(destination_endpoint, destination_provider, ssl_verify=settings["ssl_verify"])


@pytest.fixture(scope="module")
def threescale_src1(threescale):
    """Returns url for source tenant with access token with all rw rights"""
    return threescale.url_with_token


@pytest.fixture(scope="module")
def threescale_dst1(dest_client):
    """Returns url for destination tenant with access token with all rw rights"""
    return dest_client.url_with_token


@pytest.fixture(scope="module")
def policy_configs():
    """Configuration of most of the available policies."""
    return [
        rawobj.PolicyConfig("3scale_batcher", {"batch_report_seconds": 50}),
        rawobj.PolicyConfig("caching", {"caching_type": "allow"}),
        rawobj.PolicyConfig(
            "content_caching",
            {
                "rules": [
                    {
                        "cache": True,
                        "header": "X-Cache-Status",
                        "condition": {"combine_op": "and", "operations": [{"left": "oo", "op": "==", "right": "oo"}]},
                    }
                ]
            },
        ),
        rawobj.PolicyConfig(
            "headers",
            {
                "response": [
                    {
                        "op": "add",
                        "header": "X-RESPONSE-CUSTOM-ADD",
                        "value_type": "plain",
                        "value": "Additional response header",
                    }
                ],
                "request": [
                    {
                        "op": "add",
                        "header": "X-REQUEST-CUSTOM-ADD",
                        "value_type": "plain",
                        "value": "Additional request header",
                    }
                ],
                "enable": True,
            },
        ),
        rawobj.PolicyConfig(
            "ip_check", {"check-type": "whitelist", "client_ip_sources": ["X-Forwarded-For"], "ips_list": ["0.0.0.0"]}
        ),
        rawobj.PolicyConfig(
            "jwt_claim_check",
            {
                "rules": [
                    {
                        "methods": ["GET"],
                        "operations": [
                            {
                                "op": "==",
                                "jwt_claim": "azp",
                                "value": "client_id",
                                "value_type": "plain",
                                "jwt_claim_type": "plain",
                            }
                        ],
                        "combine_op": "and",
                        "resource": "/get",
                        "resource_type": "plain",
                    }
                ],
                "error_message": "error message",
            },
        ),
        rawobj.PolicyConfig("retry", {"retries": 5}),
        rawobj.PolicyConfig(
            "routing",
            {
                "rules": [
                    {
                        "url": "http://url1.org",
                        "condition": {"operations": [{"op": "==", "value": "/anything/anything", "match": "path"}]},
                        "replace_path": "{{ original_request.path | remove_first: '/anything' }}",
                    }
                ]
            },
        ),
        rawobj.PolicyConfig(
            "soap",
            {
                "mapping_rules": [
                    {"pattern": "soap_policy_action", "metric_system_name": "hits", "delta": "3"},
                    {"pattern": "soap_policy_ctype", "metric_system_name": "hits", "delta": "5"},
                ]
            },
        ),
        rawobj.PolicyConfig(
            "cors", {"allow_methods": ["GET", "POST"], "allow_credentials": True, "allow_origin": "localhost"}
        ),
        rawobj.PolicyConfig("liquid_context_debug", {}),
        rawobj.PolicyConfig("default_credentials", {"auth_type": "user_key", "user_key": "sdfsdfsofhsdkfjhjksdhf"}),
        rawobj.PolicyConfig(
            "headers",
            {
                "response": [
                    {
                        "op": "set",
                        "header": "X-RESPONSE-CUSTOM-SET",
                        "value_type": "plain",
                        "value": "Response set header",
                    }
                ],
                "request": [
                    {
                        "op": "set",
                        "header": "X-REQUEST-CUSTOM-SET",
                        "value_type": "plain",
                        "value": "Request set header",
                    }
                ],
            },
        ),
        rawobj.PolicyConfig(
            "maintenance_mode",
            {
                "message_content_type": "text/plain; charset=utf-8",
                "status": 328,
                "message": "Service Unavailable - Maintenance",
            },
        ),
        rawobj.PolicyConfig(
            "rewrite_url_captures",
            {
                "transformations": [
                    {"match_rule": "/{var_1}/{var_2}", "template": "/{var_2}?my_arg={var_1}"},
                    {"match_rule": "/{var_1}/{var_2}", "template": "/my_arg={var_2}?my_arg2={var_1}"},
                ]
            },
        ),
        rawobj.PolicyConfig("upstream_connection", {"read_timeout": 5}),
        rawobj.PolicyConfig("url_rewriting", {"commands": [{"op": "gsub", "regex": "hello", "replace": "get"}]}),
    ]
