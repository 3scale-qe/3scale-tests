"top-level conftest"

from itertools import chain
import inspect
import logging
import os
import signal
import time
import warnings

import importlib_resources as resources
import backoff
import openshift as oc
import pytest
from dynaconf.vendor.box.exceptions import BoxKeyError
from threescale_api import client, errors
from weakget import weakget

# to actually initialize all the providers
# pylint: disable=unused-import
import testsuite.capabilities.providers
import testsuite.tools

from testsuite import TESTED_VERSION, rawobj, HTTP2, gateways, configuration, resilient
from testsuite.capabilities import Capability, CapabilityRegistry
from testsuite.config import settings
from testsuite.openshift.client import OpenShiftClient

from testsuite.prometheus import PrometheusClient
from testsuite.httpx import HttpxHook
from testsuite.mockserver import Mockserver
from testsuite.toolbox import toolbox
from testsuite.utils import blame, blame_desc, warn_and_skip
from testsuite.rhsso import RHSSOServiceConfiguration, RHSSO

pytest_plugins = ("testsuite.gateway_logs",)


@pytest.fixture(scope='session', autouse=True)
def term_handler():
    """
    This will handle ^C, cleanup won't be skipped
    https://github.com/pytest-dev/pytest/issues/9142
    """
    orig = signal.signal(signal.SIGTERM, signal.getsignal(signal.SIGINT))
    yield
    signal.signal(signal.SIGTERM, orig)


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
    parser.addoption(
        "--drop-sandbag", action="store_true", default=False, help="Skip demanding/slow tests (default: False)")
    parser.addoption(
        "--sandbag", action="store_true", default=False,
        help="Run ONLY demanding/slow tests skipped by --drop-sandbag (default: False)")
    parser.addoption(
        "--drop-nopersistence", action="store_true", default=False, help="Skip tests incompatible with persistence "
                                                                         "plugin (default: False)")


# there are many branches as there are many options to influence test selection
# pylint: disable=too-many-branches
def pytest_runtest_setup(item):
    """Exclude disruptive tests by default, require explicit option"""

    marks = [i.name for i in item.iter_markers()]
    sandbag_caps = (Capability.CUSTOM_ENVIRONMENT, Capability.LOGS, Capability.JAEGER)
    if "skipif_devrelease" in marks and TESTED_VERSION.is_devrelease:
        pytest.skip("Excluding on development release")
    if "disruptive" in marks and not item.config.getoption("--disruptive"):
        pytest.skip("Excluding disruptive tests")
    if "/toolbox/" in item.nodeid and not item.config.getoption("--toolbox"):
        pytest.skip("Excluding toolbox tests")
    if "performance" in marks and not item.config.getoption("--performance"):
        pytest.skip("Excluding performance tests")
    if "/ui/" in item.nodeid and not item.config.getoption("--ui"):
        pytest.skip("Excluding UI tests")
    if item.config.getoption("--drop-sandbag"):
        if "sandbag" in marks or "xfail" in marks:
            pytest.skip("Dropping sandbag")
        elif "required_capabilities" in marks:
            required_capabilities = item.iter_markers(name="required_capabilities")
            for mark in required_capabilities:
                for cap in mark.args:
                    if cap in sandbag_caps:
                        pytest.skip("Dropping sandbag")
    if item.config.getoption("--sandbag"):
        required_capabilities = set(chain(*{m.args for m in item.iter_markers("required_capabilities")}))
        # sandbag is something marked, xfailing or having specific requirements
        if not ("sandbag" in marks or "xfail" in marks or set(sandbag_caps) & required_capabilities):
            pytest.skip("Running sandbag only")
    if item.config.getoption("--drop-nopersistence"):
        if "nopersistence" in marks:
            pytest.skip("Dropping nopersistence")
    if "required_capabilities" in marks:
        capability_marks = item.iter_markers(name="required_capabilities")
        for mark in capability_marks:
            for capability in mark.args:
                if capability not in CapabilityRegistry():
                    pytest.skip(f"Skipping test because current environment doesn't have capability {capability}")
    else:
        if Capability.APICAST not in CapabilityRegistry():
            pytest.skip(f"Skipping test because current gateway doesn't have implicit capability {Capability.APICAST}")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):  # pylint: disable=unused-argument
    """Add jira link to html report"""
    pytest_html = item.config.pluginmanager.getplugin("html")
    outcome = yield
    report = outcome.get_result()
    extra = getattr(report, "extra", [])
    if report.when == "setup":
        for marker in item.iter_markers(name="issue"):
            issue = marker.args[0]
            issue_id = issue.rstrip("/").split("/")[-1]
            extra.append(pytest_html.extras.url(issue, name=issue_id))
        report.extra = extra


@pytest.hookimpl(optionalhook=True)
def pytest_html_results_table_html(report, data):
    """Remove logs for passed tests"""
    if report.passed:
        del data[:]


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


# https://github.com/pytest-dev/pytest/issues/7767
# pylint: disable=import-outside-toplevel
def _junit_testsuite_property(config, name, value):
    """Record a property to junit on testsuite level"""

    from _pytest.junitxml import xml_key
    xml = config.stash.get(xml_key, None)
    if xml:
        xml.add_global_property(name, value)


def pytest_metadata(metadata):
    """Update testsuite metadata"""
    _settings = weakget(settings)

    testsuite_version = resources.files("testsuite").joinpath("VERSION").read_text().strip()
    version = _settings["threescale"]["version"] % testsuite_version
    namespace = _settings["openshift"]["projects"]["threescale"]["name"] % "UNKNOWN"
    ocp_version = _settings["openshift"]["version"] % ""
    if ocp_version:
        ocp_version = f"ocp{ocp_version}"

    title = os.environ.get("JOB_NAME", "Ad-hoc").split()[0]
    if "/" in title:
        title = title.split("/")[-1]  # this is due to possible job structure in jenkins
    title = _settings["reporting"]["title"] % f"{title} {namespace} {version} {ocp_version}".strip()

    admin_url = _settings["threescale"]["admin"]["url"] % "UNKNOWN"
    if _settings["fixtures"]["threescale"]["private_tenant"] % False:
        admin_url = "(private tenant created on the fly is in use)"

    metadata.update({
        "env_for_dynaconf": settings["env_for_dynaconf"],
        "testsuite-version": testsuite_version,
        "_3SCALE_TESTS_threescale__admin__url": admin_url,
        "_3SCALE_TESTS_threescale__version": version,
        "_3SCALE_TESTS_openshift__servers__default__server_url":
            _settings["openshift"]["servers"]["default"]["server_url"] % "UNKNOWN",
        "NAMESPACE": namespace,
        "polarion-testrun-title": title,
        "polarion-testrun-id": title.replace(".", "_").replace(" ", "_"),
        "polarion-testrun-status-id": "inprogress",
        "polarion-project-id": _settings["reporting"]["testsuite_properties"]["polarion_project_id"] % "None",
        "polarion-response-myteamsname":
            _settings["reporting"]["testsuite_properties"]["polarion_response_myteamsname"] % "None",
        "polarion-lookup-method": "name",
    })

    if Capability.OCP4 in CapabilityRegistry():

        metadata["_3SCALE_TESTS_threescale__gateway__OperatorApicast__openshift__project_name"] = \
            _settings["threescale"]["gateway"]["OperatorApicast"]["openshift"]["project_name"] % "None"
        metadata["_3SCALE_TESTS_threescale__apicast_operator_version"] = \
            _settings["threescale"]["apicast_operator_version"] % "UNKNOWN"
        metadata["_3SCALE_TESTS_threescale__catalogsource"] = _settings["threescale"]["catalogsource"] % "UNKNOWN"

    toolboximage = _settings["toolbox"]["podman_image"].split(':')[-1] % "UNKNOWN"
    toolboxversion = "UNKNOWN"

    if toolboximage != "UNKNOWN":
        try:
            toolboxversion = toolbox.run_cmd("-v")['stdout'].strip()
        except BoxKeyError:
            warnings.warn("Toolbox executioner is not configured")

    metadata["toolbox-version"] = toolboxversion
    metadata["_3SCALE_TESTS_toolbox__podman_image"] = toolboximage

    for key in sorted(k for k in os.environ if k.startswith("_3SCALE_TESTS")):
        ikey = key.lower()
        if "password" in ikey or "token" in ikey or "secret" in ikey or "_key" in ikey:
            metadata[f"env {key}"] = "*****"
        else:
            metadata[f"env {key}"] = os.environ[key]


# pylint: disable=protected-access
def pytest_report_header(config):
    """Report testsuite metadata"""
    header = [""]
    for key in sorted(config._metadata.keys()):
        header.append(f"testsuite: {key}={config._metadata[key]}")
        _junit_testsuite_property(config, key, config._metadata[key])
    header.append("")
    return header


@pytest.fixture(scope="module")
def logger(request):
    """Preconfigured python logger for fixtures and tests"""

    return logging.getLogger(request.node.name)


@pytest.fixture(scope="session")
def openshift(testconfig):
    "OpenShift client generator"
    return configuration.openshift


@pytest.fixture(scope="session")
def operator_apicast_openshift():
    """Creates OpenShiftClient for operator apicast project"""
    project_name = settings["threescale"]["gateway"]["OperatorApicast"]['openshift']['project_name']

    try:
        server = settings["openshift"]["servers"]['default']
    except KeyError:
        server = {}

    return OpenShiftClient(project_name=project_name,
                           server_url=server.get("server_url", None),
                           token=server.get("token", None))


# pylint: disable=too-few-public-methods,broad-except
@pytest.fixture(scope="session")
def tools(testconfig):
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
def testconfig():
    "testsuite configuration"
    return settings


@pytest.fixture(scope="session")
def threescale(testconfig, request):
    "Threescale client"

    if weakget(testconfig)["fixtures"]["threescale"]["private_tenant"] % False:
        custom_tenant = request.getfixturevalue("custom_tenant")
        tenant = custom_tenant()
        return tenant.admin_api(ssl_verify=testconfig["ssl_verify"], wait=0)

    return client.ThreeScaleClient(
        testconfig["threescale"]["admin"]["url"],
        testconfig["threescale"]["admin"]["token"],
        ssl_verify=testconfig["ssl_verify"],
        wait=0
    )


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
    account.update(
        {
            "name": iname,
            "username": iname,
            "email": f"{iname}@example.com",
            "password": account_password,
        }
    )
    account = custom_account(params=account)

    return account


@pytest.fixture(scope="session")
def custom_account(threescale, request, testconfig):
    """Parametrized custom Account

    Args:
        :param params: dict for remote call, rawobj.Account should be used
    """
    def _custom_account(params, autoclean=True, threescale_client=threescale):
        acc = resilient.accounts_create(threescale_client, params=params)
        if autoclean and not testconfig["skip_cleanup"]:
            request.addfinalizer(acc.delete)
        return acc

    return _custom_account


@pytest.fixture(scope="session")
def user(custom_user, account, request, testconfig):
    "Preconfigured user existing over whole testing session"
    username = blame(request, 'us')
    domain = testconfig["threescale"]["superdomain"]
    usr = {
        "username": username,
        "email": f"{username}@{domain}",
        "password": blame(request, ""),
        "account_id": account["id"],
    }
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
def staging_gateway(request):
    """Staging gateway"""
    gateway = gateways.gateway(staging=True)
    request.addfinalizer(gateway.destroy)
    gateway.create()

    return gateway


@pytest.fixture(scope="session")
def production_gateway(request, testconfig, openshift):
    """Production gateway"""
    if not gateways.default.HAS_PRODUCTION:
        return None

    gateway = gateways.gateway(staging=False)
    request.addfinalizer(gateway.destroy)
    gateway.create()

    return gateway


@pytest.fixture(scope="session")
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
    realm = rhsso.create_realm(blame(request, "realm"), accessTokenLifespan=24*60*60)

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

    default = weakget(testconfig)["fixtures"]["private_base_url"]["default"] % "echo_api"
    special = weakget(testconfig)["fixtures"]["private_base_url"]["special"] % "mockserver"

    def _private_base_url(kind="default"):
        kind = kind.replace("default", default).replace("special", special)
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

    def _custom_application(params, autoclean=True, hooks=None, annotate=True, account=account):
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
    return Mockserver(tools["mockserver"])


@pytest.fixture(scope="session")
def custom_tenant(testconfig, master_threescale, request):
    """
    Custom Tenant
    """
    def _custom_tenant(name="t", autoclean=True):
        user_name = blame(request, name)
        tenant = master_threescale.tenants.create(rawobj.CustomTennant(user_name))
        tenant.wait_tenant_ready()

        if autoclean and not testconfig["skip_cleanup"]:
            request.addfinalizer(tenant.delete)

        master_threescale.accounts.read_by_name(user_name).users.read_by_name(user_name).activate()

        return tenant

    return _custom_tenant


@pytest.fixture(scope="session")
def prometheus(testconfig, openshift):
    """
    Returns an instance of Prometheus client.
    Skips the tests when Prometheus is not present in the project.
    """
    threescale_namespace = weakget(settings)["openshift"]["projects"]["threescale"]["name"] % None

    if "prometheus" in testconfig and "url" in testconfig["prometheus"]:
        if "token" in testconfig["prometheus"]:
            token = testconfig["prometheus"]["token"]
        return PrometheusClient(testconfig["prometheus"]["url"], token=token, namespace=threescale_namespace)

    if not weakget(testconfig)["openshift"]["servers"]["default"] % False:
        warn_and_skip("Prometheus is not present in this project. Prometheus tests have been skipped. "
                      "Without Openshift configuration you need to set up Prometheus url. (token/namespace if needed)")

    def _prepare_prometheus_endpoint(routes):
        protocol = "https://" if "tls" in routes[0]["spec"] else "http://"
        return protocol + routes[0]['spec']['host']

    openshift_monitoring = openshift(project="openshift-monitoring")
    routes = openshift_monitoring.routes.for_service("thanos-querier")
    if len(routes) > 0:
        token = oc.whoami(cmd_args="-t")
        prometheus_url = _prepare_prometheus_endpoint(routes)
        prometheus_client = PrometheusClient(prometheus_url, True, token, threescale_namespace)
        if prometheus_client.has_metric("rails_requests_total"):
            return prometheus_client

    routes = openshift().routes.for_service('prometheus-operated')
    if len(routes) > 0:
        prometheus_url = _prepare_prometheus_endpoint(routes)
        prometheus_client = PrometheusClient(prometheus_url, True)
        if prometheus_client.has_metric("rails_requests_total"):
            return prometheus_client

    routes = openshift().routes.for_service('prometheus')
    if len(routes) > 0:
        prometheus_url = _prepare_prometheus_endpoint(routes)
        prometheus_client = PrometheusClient(prometheus_url, False)
        if prometheus_client.has_metric("rails_requests_total"):
            return prometheus_client

    warn_and_skip("Prometheus is not present in this project. Prometheus tests have been skipped.")
