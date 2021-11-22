"top-level conftest"

import inspect
import logging
import os
import time

import importlib_resources as resources
import backoff
import pytest
from threescale_api import client, errors
from weakget import weakget

# to actually initialize all the providers
# pylint: disable=unused-import
import testsuite.capabilities.providers
import testsuite.tools

from testsuite import rawobj, CONFIGURATION, HTTP2, gateways
from testsuite.capabilities import Capability, CapabilityRegistry
from testsuite.config import settings
from testsuite.prometheus import PrometheusClient
from testsuite.requestbin import RequestBinClient
from testsuite.httpx import HttpxHook
from testsuite.rhsso.objects import Realm
from testsuite.utils import blame, blame_desc, warn_and_skip
from testsuite.rhsso import RHSSOServiceConfiguration, RHSSO

pytest_plugins = ("testsuite.gateway_logs",)


def pytest_addoption(parser):
    """Add option to include disruptive tests in testrun"""

    parser.addoption(
        "--toolbox", action="store_true", default=False, help="Run also toolbox tests (default: False)")
    parser.addoption(
        "--disruptive", action="store_true", default=False, help="Run also disruptive tests (default: False)")
    parser.addoption(
        "--performance", action="store_true", default=False, help="Run also performance tests (default: False)")
    parser.addoption(
        "--ui", action="store_true", default=False, help="Run also UI tests (default: False)"
    )


def pytest_runtest_setup(item):
    """Exclude disruptive tests by default, require explicit option"""

    marks = [i.name for i in item.iter_markers()]
    if "disruptive" in marks and not item.config.getoption("--disruptive"):
        pytest.skip("Excluding disruptive tests")
    if "/toolbox/" in item.nodeid and not item.config.getoption("--toolbox"):
        pytest.skip("Excluding toolbox tests")
    if "performance" in marks and not item.config.getoption("--performance"):
        pytest.skip("Excluding performance tests")
    if "/ui/" in item.nodeid and not item.config.getoption("--ui"):
        pytest.skip("Excluding UI tests")
    if "required_capabilities" in marks:
        capability_marks = item.iter_markers(name="required_capabilities")
        for mark in capability_marks:
            for capability in mark.args:
                if capability not in CapabilityRegistry():
                    pytest.skip(f"Skipping test because current environment doesn't have capability {capability}")
    else:
        if Capability.APICAST not in CapabilityRegistry():
            pytest.skip(f"Skipping test because current gateway doesn't have implicit capability {Capability.APICAST}")


# pylint: disable=unused-argument
def pytest_collection_modifyitems(session, config, items):
    """
    Add user properties to testcases for xml output

    This adds issue and issue-id properties to junit output, utilizes
    pytest.mark.issue marker.

    This is copied from pytest examples to record custom properties in junit
    https://docs.pytest.org/en/stable/usage.html
    """

    for item in items:
        for marker in item.iter_markers(name="issue"):
            issue = marker.args[0]
            issue_id = issue.rstrip("/").split("/")[-1]
            item.user_properties.append(("issue", issue))
            item.user_properties.append(("issue-id", issue_id))


def _oc_3scale_project():
    """Just a one liner to not repeat really long line"""

    return weakget(settings)["openshift"]["projects"]["threescale"]["name"] % "UNKNOWN"


# Currently this doesn't work with xdist
# https://github.com/pytest-dev/pytest/issues/7767
# Therefore _global_property hack is present below
# **AND** therefore @fixture commented out to avoid properties
# doubled on single execution. Once xdist issue will be fixed
# this will be updated
# @pytest.fixture(scope="session", autouse=True)
def testsuite_properties(record_testsuite_property):
    """Add custom testsuite properties to junit"""

    title = os.environ.get("JOB_NAME", "Ad-hoc").split()[0]
    runid = f"{title} {_oc_3scale_project()} {settings['threescale']['version']}"
    projectid = weakget(settings)["reporting"]["testsuite_properties"]["polarion_project_id"] % "None"
    team = weakget(settings)["reporting"]["testsuite_properties"]["polarion_response_myteamsname"] % "None"

    record_testsuite_property("polarion-project-id", projectid)
    record_testsuite_property("polarion-response-myteamsname", team)
    record_testsuite_property("polarion-testrun-title", runid)
    record_testsuite_property("polarion-lookup-method", "name")


# pylint: disable=import-outside-toplevel,protected-access
def _global_property(config, name, value):
    """Temporary hack as record_global_property doesn't work with xdist"""

    from _pytest.junitxml import xml_key
    xml = config._store.get(xml_key, None)
    if xml:
        xml.add_global_property(name, value)


# pylint: disable=unused-argument
def pytest_report_header(config):
    """Add basic details about testsuite configuration"""
    testsuite_version = resources.read_text("testsuite", "VERSION").strip()
    environment = settings["env_for_dynaconf"]
    openshift = settings.get("openshift", {}).get("servers", {}).get("default", {}).get("server_url", "UNKNOWN")
    project = _oc_3scale_project()
    threescale = settings["threescale"]["admin"]["url"]
    version = settings["threescale"]["version"]
    catalogsource = weakget(settings)["threescale"]["catalogsource"] % "UNKNOWN"

    title = os.environ.get("JOB_NAME", "Ad-hoc").split()[0]
    if "/" in title:
        title = title.split("/")[-1]  # this is due to possible job structure in jenkins
    title = f"{title} {_oc_3scale_project()} {settings['threescale']['version']}"
    projectid = weakget(settings)["reporting"]["testsuite_properties"]["polarion_project_id"] % "None"
    team = weakget(settings)["reporting"]["testsuite_properties"]["polarion_response_myteamsname"] % "None"

    _global_property(config, "openshift-url", openshift)
    _global_property(config, "openshift-namespace", project)
    _global_property(config, "openshift-catalogsource", catalogsource)
    _global_property(config, "testsuite-version", testsuite_version)
    _global_property(config, "polarion-project-id", projectid)
    _global_property(config, "polarion-response-myteamsname", team)
    _global_property(config, "polarion-testrun-title", title)
    _global_property(config, "polarion-testrun-id", title.replace(".", "_"))
    _global_property(config, "polarion-testrun-status-id", "inprogress")
    _global_property(config, "polarion-lookup-method", "name")

    return [
        "",
        f"testsuite: testsuite version = {testsuite_version}",
        f"testsuite: environment = {environment}",
        f"testsuite: openshift = {openshift}",
        f"testsuite: project = {project}",
        f"testsuite: threescale = {threescale}",
        f"testsuite: for 3scale version = {version}",
        f"testsuite: catalogsource = {catalogsource}",
        ""]


@pytest.fixture(scope="module")
def logger(request):
    """Preconfigured python logger for fixtures and tests"""

    return logging.getLogger(request.node.name)


@pytest.fixture(scope="session")
def openshift(configuration):
    "OpenShift client generator"
    return configuration.openshift


# pylint: disable=too-few-public-methods,broad-except
@pytest.fixture(scope="session")
def tools(testconfig, configuration):
    """dict-like object to provide testing environment tools"""

    options = weakget(testconfig)["fixtures"]["tools"] % {"namespace": "tools"}

    def _init_source(klass):
        """dynamic __init__ args introspection"""

        init_args = inspect.signature(klass.__init__).parameters.keys()
        init_args -= ['self', 'args', 'kwargs']
        if len(init_args) == 0:
            return klass()
        init_args = {k: v for k, v in options.items() if k in init_args}
        if len(init_args) == 0:
            return klass()
        return klass(**init_args)

    class _Tools:
        def __init__(self, sources):
            self._sources = sources

        def __getitem__(self, name):
            for source in self._sources:
                try:
                    value = source[name]
                    if value is not None:
                        return value
                except Exception:
                    pass
            raise KeyError(name)

    sources = options.get("sources", ["Rhoam", "OpenshiftProject", "Settings"])
    sources = [_init_source(getattr(testsuite.tools, t)) for t in sources]
    return _Tools(sources)


@pytest.fixture(scope="module")
def prod_client(production_gateway, application, request):
    """Prepares application and service for production use and creates new production client

    Parameters:
        app (Application): Application for which create the client.
        promote (bool): If true, then this method also promotes proxy configuration to production.
        version (int): Proxy configuration version of service to promote.
        redeploy (bool): If true, then the production gateway will be reloaded

    Returns:
        api_client (HttpClient): Api client for application

    """
    def _prod_client(app=application, promote: bool = True, version: int = -1, redeploy: bool = True):
        if promote:
            if version == -1:
                version = app.service.proxy.list().configs.latest()['version']
            app.service.proxy.list().promote(version=version)
        if redeploy:
            production_gateway.reload()

        client = app.api_client(endpoint="endpoint")
        request.addfinalizer(client.close)
        return client

    return _prod_client


@pytest.fixture(scope="session")
def configuration():
    "CommonConfiguration instance"
    return CONFIGURATION


@pytest.fixture(scope="session")
def testconfig():
    "testsuite configuration"
    return settings


@pytest.fixture(scope="session")
def threescale(testconfig):
    "Threescale client"

    return client.ThreeScaleClient(
        testconfig["threescale"]["admin"]["url"],
        testconfig["threescale"]["admin"]["token"],
        ssl_verify=testconfig["ssl_verify"])


@pytest.fixture(scope="session")
def master_threescale(testconfig):
    """Threescale client using master url and token"""

    return client.ThreeScaleClient(
        testconfig["threescale"]["master"]["url"],
        testconfig["threescale"]["master"]["token"],
        ssl_verify=testconfig["ssl_verify"])


@pytest.fixture(scope="session")
def account_password():
    """Default password for Accounts"""
    return '123456'


@pytest.fixture(scope="session")
def account(custom_account, request, testconfig, account_password):
    "Preconfigured account existing over whole testing session"
    iname = blame(request, "id")
    account = rawobj.Account(org_name=iname, monthly_billing_enabled=None, monthly_charging_enabled=None)
    account.update(dict(
        name=iname, username=iname,
        email=f"{iname}@anything.invalid",
        password=account_password))
    account = custom_account(params=account)

    return account


@pytest.fixture(scope="session")
def custom_account(threescale, request, testconfig):
    """Parametrized custom Account

    Args:
        :param params: dict for remote call, rawobj.Account should be used
    """
    @backoff.on_exception(backoff.fibo, errors.ApiClientError, 8, jitter=None)
    def _custom_account(params, autoclean=True, threescale_client=threescale):
        acc = threescale_client.accounts.create(params=params)
        if autoclean and not testconfig["skip_cleanup"]:
            request.addfinalizer(acc.delete)
        return acc

    return _custom_account


@pytest.fixture(scope="session")
def user(custom_user, account, request, testconfig, configuration):
    "Preconfigured user existing over whole testing session"
    username = blame(request, 'us')
    domain = configuration.superdomain
    usr = dict(username=username, email=f"{username}@{domain}",
               password=blame(request, ''), account_id=account['id'])
    usr = custom_user(account, params=usr)

    return usr


@pytest.fixture(scope="session")
def custom_user(request, testconfig):  # pylint: disable=unused-argument
    """Parametrized custom User

    Args:
        :param params: dict for remote call, rawobj.User should be used
    """

    def _custom_user(cus_account, params, autoclean=True):
        usr = cus_account.users.create(params=params)
        if autoclean and not testconfig["skip_cleanup"]:
            def finalizer():
                usr.delete()
            request.addfinalizer(finalizer)
        return usr

    return _custom_user


@pytest.fixture(scope="module")
def provider_account(threescale):
    """Returns current Provider Account (current Tenant)"""
    return threescale.provider_accounts.fetch()


@pytest.fixture(scope="module")
def provider_account_user(custom_provider_account_user, account_password, request):
    """Preconfigured provider account existing over whole testing session"""
    username = blame(request, 'pa')
    user = rawobj.AccountUser(username=username, email=f"{username}@example.com", password=account_password)
    user = custom_provider_account_user(user)

    return user


@pytest.fixture(scope="module")
def custom_provider_account_user(request, threescale, testconfig):
    """Parametrized custom Provider account user
    Args:
        :param params: dict for remote call, rawobj.AccountUser should be used
    """
    def _custom_user(params, autoclean=True):
        user = threescale.provider_account_users.create(params=params)
        if autoclean and not testconfig["skip_cleanup"]:
            request.addfinalizer(user.delete)
        return user

    return _custom_user


@pytest.fixture(scope="session")
def staging_gateway(request, testconfig, configuration):
    """Staging gateway"""
    options = gateways.configuration.options(staging=True,
                                             settings_block=testconfig["threescale"]["gateway"]["configuration"],
                                             configuration=configuration)
    gateway = gateways.configuration.staging(options)
    request.addfinalizer(gateway.destroy)

    gateway.create()

    return gateway


@pytest.fixture(scope="session")
def production_gateway(request, testconfig, configuration):
    """Production gateway"""
    gateway = gateways.configuration.production
    if gateway is None:
        return None
    options = gateways.configuration.options(staging=False,
                                             settings_block=testconfig["threescale"]["gateway"]["configuration"],
                                             configuration=configuration)
    gateway = gateway(options)
    request.addfinalizer(gateway.destroy)

    gateway.create()

    return gateway


@pytest.fixture(scope="module")
def rhsso_service_info(request, testconfig, tools):
    """
    Set up client for zync
    :return: dict with all important details
    """
    cnf = testconfig["rhsso"]
    assert cnf["password"] is not None, "SSO admin password neither discovered not set in config"
    rhsso = RHSSO(server_url=tools["no-ssl-sso"],
                  username=cnf["username"],
                  password=cnf["password"])
    realm: Realm = rhsso.create_realm(blame(request, "realm"), accessTokenLifespan=24*60*60)

    if not testconfig["skip_cleanup"]:
        request.addfinalizer(realm.delete)

    client = realm.create_client(
        name=blame(request, "client"),
        serviceAccountsEnabled=True,
        directAccessGrantsEnabled=False,
        publicClient=False,
        protocol="openid-connect",
        standardFlowEnabled=False)

    username = cnf["test_user"]["username"]
    password = cnf["test_user"]["password"]
    user = realm.create_user(username, password)

    client.assign_role("manage-clients")

    return RHSSOServiceConfiguration(rhsso, realm, client, user, username, password)


@pytest.fixture(scope="module")
def service_proxy_settings(private_base_url):
    "dict of proxy settings to be used when service created"
    return rawobj.Proxy(private_base_url())


@pytest.fixture(scope="module")
def private_base_url(testconfig, tools):
    """URL to API backend.

    This is callable fixture with parameter `kind`.
    `kind="primary"` returns backend to be used primarily/by default.

    Args:
        :param kind: Desired type of backend; possible values 'primary' (default), 'httpbin', 'echo-api'"""

    primary = weakget(testconfig)["fixtures"]["private_base_url"]["default"] % "echo_api"

    def _private_base_url(kind="primary"):
        if kind == "primary":
            kind = primary
        return tools[kind]

    return _private_base_url


@pytest.fixture(scope="module")
def service_settings(request):
    "dict of service settings to be used when service created"
    return {"name": blame(request, "svc")}


@pytest.fixture(scope="module")
def lifecycle_hooks(request, testconfig):
    """List of objects with hooks into app/svc creation and deletion

    Hooks should implement methods defined and documented in testsuite.lifecycle_hook.LifecycleHook
    or should inherit from that class"""

    defaults = testconfig.get("fixtures", {}).get("lifecycle_hooks", {}).get("defaults")
    if defaults is not None:
        return [request.getfixturevalue(i) for i in defaults]
    return []


@pytest.fixture(scope="session")
def httpx():
    """Httpx fixture that returns lifecycle hook for httpx"""
    return HttpxHook(HTTP2)


@pytest.fixture(scope="module")
def service(backends_mapping, custom_service, service_settings, service_proxy_settings, lifecycle_hooks):
    "Preconfigured service with backend defined existing over whole testsing session"
    return custom_service(service_settings, service_proxy_settings, backends_mapping, hooks=lifecycle_hooks)


@pytest.fixture(scope="module")
def application(service, custom_application, custom_app_plan, lifecycle_hooks, request):
    "application bound to the account and service existing over whole testing session"
    plan = custom_app_plan(rawobj.ApplicationPlan(blame(request, "aplan")), service)
    app = custom_application(rawobj.Application(blame(request, "app"), plan), hooks=lifecycle_hooks)
    service.proxy.deploy()
    return app


@pytest.fixture(scope="module")
def api_client(application, request):
    """
    Fixture that returns api_client
    Parameters:
        app (Application): Application for which create the client.
    Returns:
        api_client (HttpClient): Api client for application
    """
    def _api_client(app=application, **kwargs):
        client = app.api_client(**kwargs)
        request.addfinalizer(client.close)
        return client

    return _api_client


@pytest.fixture(scope="module")
def custom_app_plan(custom_service, service_proxy_settings, request, testconfig):
    """Parametrized custom Application Plan

    Args:
        :param params: dict for remote call, rawobj.ApplicationPlan should be used
        :param service: Service object for which plan should be created"""
    plans = []

    def _custom_app_plan(params, service=None, autoclean=True):
        if service is None:
            service = custom_service({"name": blame(request, "svc")}, service_proxy_settings)
        plan = service.app_plans.create(params=params)
        if autoclean:
            plans.append(plan)
        return plan

    if not testconfig["skip_cleanup"]:
        request.addfinalizer(lambda: [item.delete() for item in plans])

    return _custom_app_plan


@pytest.fixture(scope="module")
def oas3_body(fil=resources.files('testsuite.resources.oas3').joinpath('petstore-expanded.json')):
    """Loads OAS3 file to string"""
    return fil.read_text()


@pytest.fixture(scope="module")
def active_doc(request, service, oas3_body, custom_active_doc):
    """Active doc. bound to service."""
    return custom_active_doc(
        rawobj.ActiveDoc(blame(request, "activedoc"), oas3_body, service=service))


@pytest.fixture(scope="module")
def custom_active_doc(threescale, testconfig, request):
    """Parametrized custom Active document

    Args:
        :param service: Service object for which active doc. should be created
        :param body: OAS body - string
    """

    ads = []

    def _custom_active_doc(params, autoclean=True, threescale_client=threescale):
        acd = threescale_client.active_docs.create(params=params)
        if autoclean:
            ads.append(acd)
        return acd

    if not testconfig["skip_cleanup"]:
        request.addfinalizer(lambda: [item.delete() for item in ads])

    return _custom_active_doc


def _select_hooks(hook, hooks):
    """Returns list of callable hooks of given name"""

    if not hooks:
        return ()
    return [getattr(i, hook) for i in hooks if hasattr(i, hook)]


# custom_app_plan dependency is needed to ensure cleanup in correct order
@pytest.fixture(scope="module")
def custom_application(account, custom_app_plan, request, testconfig):  # pylint: disable=unused-argument
    """Parametrized custom Application

    Args:
        :param params: dict for remote call, rawobj.Application should be used
        :param hooks: List of objects implementing necessary methods from testsuite.lifecycle_hook.LifecycleHook

    (Typical) Usage:
        plan = custom_app_plan(rawobj.ApplicationPlan("CustomPlan"), service)
        app = custom_application(rawobj.Application("CustomApp", plan))
    """

    def _custom_application(params, autoclean=True, hooks=None, annotate=True):
        params = params.copy()
        for hook in _select_hooks("before_application", hooks):
            params = hook(params)

        if annotate:
            params["description"] = blame_desc(request, params.get("description"))

        app = account.applications.create(params=params)

        if autoclean and not testconfig["skip_cleanup"]:
            def finalizer():
                for hook in _select_hooks("on_application_delete", hooks):
                    try:
                        hook(app)
                    except Exception:  # pylint: disable=broad-except
                        pass
                app.delete()
            request.addfinalizer(finalizer)

        app.api_client_verify = testconfig["ssl_verify"]

        for hook in _select_hooks("on_application_create", hooks):
            hook(app)

        return app

    return _custom_application


@pytest.fixture(scope="module")
def backends_mapping():
    """
    Due to the new 3Scale feature, we need to be able to create  custom backends and backend usages and then pass them
    to creation of custom service. By default, it does nothing, just lets you skip creating a backend in test files.
    """
    return {}


@pytest.fixture(scope="module")
def custom_service(threescale, request, testconfig, logger):
    """Parametrized custom Service

    Args:
        :param params: dict for remote call
        :param proxy_params: dict of proxy options for remote call, rawobj.Proxy should be used
        :param hooks: List of objects implementing necessary methods from testsuite.lifecycle_hook.LifecycleHook"""

    # pylint: disable=too-many-arguments
    def _custom_service(params, proxy_params=None, backends=None, autoclean=True,
                        hooks=None, annotate=True, threescale_client=threescale):
        params = params.copy()
        for hook in _select_hooks("before_service", hooks):
            params = hook(params)

        if annotate:
            params["description"] = blame_desc(request, params.get("description"))

        svc = threescale_client.services.create(params=params)

        if autoclean and not testconfig["skip_cleanup"]:
            def finalizer():
                for hook in _select_hooks("on_service_delete", hooks):
                    try:
                        hook(svc)
                    except Exception:  # pylint: disable=broad-except
                        pass

                implicit = []
                if not backends and proxy_params:  # implicit backend created
                    bindings = svc.backend_usages.list()
                    bindings = [svc.threescale_client.backends[i["backend_id"]] for i in bindings]
                    implicit = [
                        i for i in bindings
                        if i["name"] == f"{svc['name']} Backend"
                        and i["description"] == f"Backend of {svc['name']}"]

                svc.delete()

                try:
                    if len(implicit) == 1:
                        _backend_delete(implicit[0])
                    else:
                        logger.debug("Unexpected count of candidates for implicit backend: %s", str(implicit))
                except Exception as err:  # pylint: disable=broad-except
                    logger.debug("An error occurred during attempt to delete implicit backend: %s", str(err))

            request.addfinalizer(finalizer)

        # Due to asynchronous nature of 3scale the proxy is not always ready immediately,
        # this is not necessarily bug of 3scale but we need to compensate for it regardless
        time.sleep(1)
        if backends:
            for path, backend in backends.items():
                svc.backend_usages.create({"path": path, "backend_api_id": backend["id"]})
            proxy_params = {}
            for hook in _select_hooks("before_proxy", hooks):
                proxy_params = hook(svc, proxy_params)

            svc.proxy.list().update(params=proxy_params)
        elif proxy_params:
            for hook in _select_hooks("before_proxy", hooks):
                proxy_params = hook(svc, proxy_params)

            svc.proxy.update(params=proxy_params)
        svc.proxy.deploy()

        for hook in _select_hooks("on_service_create", hooks):
            hook(svc)

        return svc

    return _custom_service


@backoff.on_exception(backoff.fibo, errors.ApiClientError, max_tries=8, jitter=None)
def _backend_delete(backend):
    """reliable backend delete"""

    backend.delete()


@pytest.fixture(scope="module")
# pylint: disable=too-many-arguments
def custom_backend(threescale, request, testconfig, private_base_url):
    """
    Parametrized custom Backend
    Args:
        :param name: name of backend
        :param endpoint: endpoint of backend
    """

    def _custom_backend(name="be", endpoint=None, autoclean=True, hooks=None, threescale_client=threescale,
                        blame_name=True):
        if endpoint is None:
            endpoint = private_base_url()

        if blame_name:
            name = blame(request, name, 10)

        params = {"name": name, "private_endpoint": endpoint}

        for hook in _select_hooks("before_backend", hooks):
            hook(params)

        backend = threescale_client.backends.create(params=params)

        if autoclean and not testconfig["skip_cleanup"]:
            def finalizer():
                for hook in _select_hooks("on_backend_delete", hooks):
                    try:
                        hook(backend)
                    except Exception:  # pylint: disable=broad-except
                        pass
                _backend_delete(backend)
            request.addfinalizer(finalizer)

        for hook in _select_hooks("on_backend_create", hooks):
            hook(backend)

        return backend

    return _custom_backend


@pytest.fixture(scope="module")
def requestbin(testconfig, tools):
    """
    Returns an instance of RequestBin.
    """
    return RequestBinClient(weakget(testconfig)["requestbin"]["url"] % tools["request-bin"])


@pytest.fixture(scope="session")
def custom_tenant(testconfig, master_threescale, request):
    """
    Custom Tenant
    """
    def _custom_tenant(name="t", autoclean=True, wait=True):
        user_name = blame(request, name)
        tenant = master_threescale.tenants.create(rawobj.CustomTennant(user_name))

        if autoclean and not testconfig["skip_cleanup"]:
            request.addfinalizer(tenant.delete)

        master_threescale.accounts.read_by_name(user_name).users.read_by_name(user_name).activate()

        if wait:
            admin_base_url = tenant.entity["signup"]["account"]["admin_base_url"]
            access_token = tenant.entity["signup"]["access_token"]["value"]

            unprivileged_client = client.ThreeScaleClient(admin_base_url, access_token, ssl_verify=False)

            @backoff.on_exception(backoff.fibo, errors.ApiClientError, max_tries=8, jitter=None)
            def _wait_on_ready_tenant():
                unprivileged_client.services.list()

            _wait_on_ready_tenant()

        return tenant

    return _custom_tenant


@pytest.fixture(scope="session")
def prometheus(testconfig, openshift):
    """
    Returns an instance of Prometheus client.
    Skips the tests when Prometheus is not present in the project.
    """
    if "prometheus" in testconfig:
        return PrometheusClient(testconfig["prometheus"]["url"])

    routes = openshift().routes.for_service('prometheus-operated')
    if len(routes) == 0:
        routes = openshift().routes.for_service('prometheus')

    if len(routes) == 0:
        warn_and_skip("Prometheus is not present in this project. Prometheus tests have been skipped.")

    protocol = "https://" if "tls" in routes[0]["spec"] else "http://"
    prometheus_url = protocol + routes[0]['spec']['host']

    return PrometheusClient(prometheus_url)
