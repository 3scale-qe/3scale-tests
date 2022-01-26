"provide fixtures for custom policy through operator testing"
import pytest
import backoff

from testsuite import rawobj
from testsuite.utils import blame
from testsuite.openshift.objects import Secrets


@pytest.fixture(scope="module")
def secrets(openshift):
    """Interface to return the dict-like Secrets
    """
    return Secrets(openshift())


@pytest.fixture(scope="module")
def delete_secret(secrets):
    """Delete the secret containing the policy after execution
    """
    yield
    del secrets["policy"]


# pylint: disable=unused-argument
@pytest.fixture(scope="module")
def create_custom_policy_secret(secrets, delete_secret):
    """Create an openshift secrets to use as custom policy based on https://github.com/3scale-qe/apicast-example-policy
    """
    initlua = "return require('example')"
    apicastpolicyjson = """
    {
        "$schema": "http://apicast.io/policy-v1/schema#manifest#",
        "name": "APIcast Example Policy",
        "summary": "This is just an example.",
        "description": "This policy is just an example how to write your custom policy.",
        "version": "0.1",
        "configuration": {
            "type": "object",
            "properties": { }
        }
    }
    """
    examplelua = """
    local setmetatable = setmetatable

    local _M = require('apicast.policy').new('Example', '0.1')
    local mt = { __index = _M }

    function _M.new()
    return setmetatable({}, mt)
    end

    function _M:init()
    ngx.log(ngx.DEBUG, "example policy initialized")
    -- do work when nginx master process starts
    end

    function _M:init_worker()
    -- do work when nginx worker process is forked from master
    end

    function _M:rewrite()
    -- change the request before it reaches upstream
    ngx.req.set_header('X-Example-Policy-Request', 'HERE')
    end

    function _M:access()
    -- ability to deny the request before it is sent upstream
    end

    function _M:content()
    -- can create content instead of connecting to upstream
    end

    function _M:post_action()
    -- do something after the response was sent to the client
    end

    function _M:header_filter()
    -- can change response headers
    ngx.header['X-Example-Policy-Response'] = 'TEST'
    end

    function _M:body_filter()
    -- can read and change response body
    -- https://github.com/openresty/lua-nginx-module/blob/master/README.markdown#body_filter_by_lua
    end

    function _M:log()
    -- can do extra logging
    end

    function _M:balancer()
    -- use for example require('resty.balancer.round_robin').call to do load balancing
    end

    return _M
    """
    policydict = {
        "init.lua": initlua,
        "example.lua": examplelua,
        "apicast-policy.json": apicastpolicyjson
    }

    secrets.create(name="policy", string_data=policydict)
    return secrets


# pylint: disable=unused-argument
@pytest.fixture(scope="module")
def patch_apimanager(request, openshift, create_custom_policy_secret):
    """Patch the apimanager CRD to add the custom policy added to apicast staging
    """
    apimanager = openshift().api_manager
    # TODO: do it through apimanager.set_path but it looks not working at this time
    openshift().patch("APIManager", apimanager.name(),
                      patch={"spec":
                             {"apicast":
                              {"stagingSpec":
                               {"customPolicies": [
                                {"name":
                                    "example",
                                    "version": "0.1",
                                    "secretRef":
                                    {"name": "policy"}
                                 }],
                                "replicas": 1
                                }}}}, patch_type="merge")
    request.addfinalizer(lambda: openshift().patch("APIManager", apimanager.name(),
                         patch={"spec":
                                {"apicast": {
                                    "stagingSpec": {
                                        "customPolicies": []
                                    }
                                }}}, patch_type="merge"))

    @backoff.on_predicate(backoff.fibo, max_tries=10)
    def wait_for_starting(apimanager):
        """Check that apicast-staging is not in ready state
        """
        return not apimanager.ready({"apicast-staging"})

    @backoff.on_predicate(backoff.fibo, max_tries=10)
    def wait_for_ready(apimanager):
        """Waiting for both apicast being in readdy state
           to ensure that the whole apimanager is up and running
        """
        return apimanager.ready({"apicast-staging", "apicast-production"})

    # We need to explicitly wait for the deployment being in starting state
    # before waiting for it to be ready, the operator needs time to reconcile
    # its state
    wait_for_starting(apimanager)
    wait_for_ready(apimanager)


@pytest.fixture(scope="module")
def service_settings(request) -> dict:
    "dict of service settings to be used when service created"
    return {"name": blame(request, "svc")}


# pylint: disable=too-many-arguments, too-many-instance-attributes
@pytest.fixture(scope="module")
def service(backends_mapping, custom_service, service_settings,
            service_proxy_settings, lifecycle_hooks) -> dict:
    "Preconfigured service with backend defined existing over whole testing session"
    svc = custom_service(service_settings, service_proxy_settings, backends_mapping, hooks=lifecycle_hooks)
    svc.proxy.list().policies.append(rawobj.PolicyConfig("example", configuration={}, version="0.1"))
    return svc


@pytest.fixture(scope="module")
def application(service, custom_application, custom_app_plan,
                lifecycle_hooks, request) -> dict:
    "application bound to the account and service existing over whole testing session"
    plan = custom_app_plan(rawobj.ApplicationPlan(blame(request, "aplan")), service)
    app = custom_application(rawobj.Application(blame(request, "app"), plan), hooks=lifecycle_hooks)
    service.proxy.deploy()
    return app
