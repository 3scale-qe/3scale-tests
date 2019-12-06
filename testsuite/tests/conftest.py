"top-level conftest"
import os
import time

import pytest
import threescale_api

import urllib3

import openshift as oc
from dynaconf import settings
from threescale_api import client
import testsuite.gateways as gateways

from testsuite import rawobj
from testsuite.openshift.client import OpenShiftClient
from testsuite.utils import randomize, retry_for_session
from testsuite.rhsso.rhsso import RHSSOServiceConfiguration, RHSSO, add_realm_management_role, create_rhsso_user

if settings["ignore_insecure_ssl_warning"]:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

if settings["ssl_verify"] and "REQUESTS_CA_BUNDLE" not in os.environ:
    for ca_bundle in (
            "/etc/pki/tls/certs/ca-bundle.crt",
            "/etc/ca-certificates/extracted/ca-bundle.trust.crt",
            "/etc/ssl/certs/ca-certificates.crt"):
        if os.path.exists(ca_bundle):
            os.environ["REQUESTS_CA_BUNDLE"] = ca_bundle
            break


# Monkey-patch for HTTP/2, needs to be fixed with  plugable api_client for application
if settings["http2"]:
    threescale_api.utils.HttpClient.retry_for_session = staticmethod(retry_for_session)


def pytest_addoption(parser):
    """Add option to include disruptive tests in testrun"""
    parser.addoption(
        "--disruptive", action="store_true", default=False, help="Run also disruptive tests (default: False)")


def pytest_runtest_setup(item):
    """Exclude disruptive tests by default, require explicit option"""

    marks = [i.name for i in item.iter_markers()]
    if "disruptive" in marks and not item.config.getoption("--disruptive"):
        pytest.skip("Excluding disruptive tests")
    if "required_capabilities" in marks:
        capability_marks = item.iter_markers(name="required_capabilities")
        for mark in capability_marks:
            for capability in mark.args:
                if capability not in gateways.CAPABILITIES:
                    pytest.skip(f"Skipping test because current gateway doesn't have capability {capability}")


# pylint: disable=unused-argument
def pytest_report_header(config):
    """Add basic details about testsuite configuration"""

    environment = settings["env_for_dynaconf"]
    openshift = settings["openshift"]["servers"]["default"]["server_url"]
    project = settings["openshift"]["projects"]["threescale"]["name"]

    threescale = "{dynamic}"

    try:
        threescale = settings["threescale"]["admin"]["url"]
    except KeyError:
        pass

    return [
        "",
        f"testsuite: environment = {environment}",
        f"testsuite: openshift = {openshift}",
        f"testsuite: project = {project}",
        f"testsuite: threescale = {threescale}",
        ""]


@pytest.fixture(scope="session")
def openshift(testconfig):
    "OpenShift client generator"
    servers = testconfig["openshift"]["servers"]
    projects = testconfig["openshift"]["projects"]

    def _client(server_name: str = "default", project_name: str = "threescale") -> OpenShiftClient:
        if server_name not in servers:
            raise AttributeError("Server %s is not defined in configuration" % server_name)
        if project_name not in projects:
            raise AttributeError("Project %s is not defined in configuration" % project_name)
        server = servers[server_name]
        return OpenShiftClient(project_name=projects[project_name]["name"],
                               server_url=server.get("server_url", None),
                               token=server.get("token", None))
    return _client


@pytest.fixture(scope="module")
def prod_client(testconfig, production_gateway, application):
    """Prepares application and service for production use and creates new production client

    Parameters:
        app (Application): Application for which create the client.
        promote (bool): If true, then this method also promotes proxy configuration to production.
        version (int): Proxy configuration version of service to promote.
        redeploy (bool): If true, then the production gateway will be reloaded

    Returns:
        api_client (HttpClient): Api client for application

    """
    def _prod_client(app=application, promote: bool = True, version: int = 1, redeploy: bool = True):
        if promote:
            app.service.proxy.list().promote(version=version)
        if redeploy:
            production_gateway.reload()

        return app.api_client(endpoint="endpoint")

    return _prod_client


@pytest.fixture(scope="session")
def testconfig():
    "testsuite configuration"
    return settings


@pytest.fixture(scope="session")
def threescale(testconfig, openshift):
    "Threescale client"

    oc_error = None

    try:
        try:
            token = testconfig["threescale"]["admin"]["token"]
        except KeyError:
            token = openshift().secrets["system-seed"]["ADMIN_ACCESS_TOKEN"]

        try:
            url = testconfig["threescale"]["admin"]["url"]
        except KeyError:
            route = openshift().routes.for_service("system-provider")[0]
            url = "https://" + route["spec"]["host"]
    except oc.OpenShiftPythonException as err:
        oc_error = err.result.as_dict()["actions"][0]["err"]

    # This is needed because pytest tracks all the tracebacks back and prints them all.
    # Raising this from except would print much much more.
    if oc_error:
        raise Exception(f"(From Openshift) {oc_error}")

    verify = testconfig["ssl_verify"]
    return client.ThreeScaleClient(url, token, ssl_verify=verify)


@pytest.fixture(scope="session")
def account(threescale, request, testconfig):
    "Preconfigured account existing over whole testing session"
    name = randomize("account")
    account = dict(name=name, username=name, org_name=name)
    account = threescale.accounts.create(params=account)

    if not testconfig["skip_cleanup"]:
        request.addfinalizer(account.delete)

    return account


@pytest.fixture(scope="session")
def staging_gateway(request, testconfig, openshift):
    """Staging gateway"""
    configuration = testconfig["threescale"]["gateway"]["configuration"]
    gateway = gateways.CLASSES["staging"](configuration=configuration, openshift=openshift, staging=True)
    gateway.create()

    request.addfinalizer(gateway.destroy)
    return gateway


@pytest.fixture(scope="session")
def production_gateway(request, testconfig, openshift):
    """Production gateway"""
    configuration = testconfig["threescale"]["gateway"]["configuration"]
    gateway = gateways.CLASSES["production"]
    if gateway is None:
        raise NotImplementedError()
    gateway = gateway(configuration=configuration, openshift=openshift, staging=False)
    gateway.create()

    request.addfinalizer(gateway.destroy)
    return gateway


@pytest.fixture(scope="module")
def rhsso_service_info(request, testconfig):
    """
    Set up client for zync
    :return: dict with all important details
    """
    cnf = testconfig["rhsso"]
    rhsso = RHSSO(server_url=cnf["url"],
                  username=cnf["username"],
                  password=cnf["password"])
    realm = rhsso.create_realm(randomize("realm"))

    if not testconfig["skip_cleanup"]:
        request.addfinalizer(realm.delete)

    client = realm.clients.create(id=randomize("client"), serviceAccountsEnabled=True, standardFlowEnabled=False)

    username = cnf["test_user"]["username"]
    password = cnf["test_user"]["password"]
    user = create_rhsso_user(realm, username, password)

    add_realm_management_role("manage-clients", client, realm)

    return RHSSOServiceConfiguration(rhsso, realm, client, user)


@pytest.fixture(scope="module")
def service_proxy_settings(private_base_url):
    "dict of proxy settings to be used when service created"
    return rawobj.Proxy(private_base_url())


@pytest.fixture(scope="module")
def private_base_url(testconfig):
    """URL to API backend.

    This is callable fixture with parameter `kind`.
    `kind="primary"` returns backend to be used primarily/by default.

    Args:
        :param kind: Desired type of backend; possible values 'primary' (default), 'httpbin', 'echo-api'"""

    def _private_base_url(kind="primary"):
        return testconfig["threescale"]["service"]["backends"][kind]

    return _private_base_url


@pytest.fixture(scope="module")
def service_settings():
    "dict of service settings to be used when service created"
    return {"name": randomize("service")}


@pytest.fixture(scope="module")
def lifecycle_hooks():
    """List of objects with hooks into app/svc creation and deletion

    Hooks should implement methods defined and documented in testsuite.lifecycle_hook.LifecycleHook
    or should inherit from that class"""

    return []


@pytest.fixture(scope="module")
def service(backends_mapping, custom_service, service_settings, service_proxy_settings, lifecycle_hooks):
    "Preconfigured service with backend defined existing over whole testsing session"
    return custom_service(service_settings, service_proxy_settings, backends_mapping, hooks=lifecycle_hooks)


@pytest.fixture(scope="module")
def application(service, custom_application, custom_app_plan, lifecycle_hooks):
    "application bound to the account and service existing over whole testing session"
    plan = custom_app_plan(rawobj.ApplicationPlan(randomize("AppPlan")), service)
    return custom_application(rawobj.Application(randomize("App"), plan), hooks=lifecycle_hooks)


@pytest.fixture(scope="module")
def api_client(application):
    "Make calls to exposed API"
    return application.api_client()


@pytest.fixture(scope="module")
def custom_app_plan(custom_service, service_proxy_settings, request, testconfig):
    """Parametrized custom Application Plan

    Args:
        :param params: dict for remote call, rawobj.ApplicationPlan should be used
        :param service: Service object for which plan should be created"""
    plans = []

    def _custom_app_plan(params, service=None, autoclean=True):
        if service is None:
            service = custom_service({"name": randomize("service")}, service_proxy_settings)
        plan = service.app_plans.create(params=params)
        if autoclean:
            plans.append(plan)
        return plan

    if not testconfig["skip_cleanup"]:
        request.addfinalizer(lambda: [item.delete() for item in plans])

    return _custom_app_plan


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

    def _custom_application(params, autoclean=True, hooks=None):
        for hook in _select_hooks("before_application", hooks):
            params = hook(params)

        app = account.applications.create(params=params)

        if autoclean and not testconfig["skip_cleanup"]:
            def finalizer():
                for hook in _select_hooks("on_application_delete", hooks):
                    try:
                        hook(app)
                    finally:
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
def custom_service(threescale, request, testconfig, staging_gateway):
    """Parametrized custom Service

    Args:
        :param params: dict for remote call
        :param proxy_params: dict of proxy options for remote call, rawobj.Proxy should be used
        :param hooks: List of objects implementing necessary methods from testsuite.lifecycle_hook.LifecycleHook"""

    def _custom_service(params, proxy_params=None, backends=None, autoclean=True, hooks=None):
        for hook in _select_hooks("before_service", hooks):
            params, proxy_params = hook(params, proxy_params)

        svc = threescale.services.create(params=staging_gateway.get_service_settings(params))

        if autoclean and not testconfig["skip_cleanup"]:
            def finalizer():
                for hook in _select_hooks("on_service_delete", hooks):
                    try:
                        hook(svc)
                    finally:
                        pass
                svc.delete()
            request.addfinalizer(finalizer)

        # Due to asynchronous nature of 3scale the proxy is not always ready immediately,
        # this is not necessarily bug of 3scale but we need to compensate for it regardless
        time.sleep(1)
        if backends:
            for path, backend in backends.items():
                svc.backend_usages.create({"path": path, "backend_api_id": backend["id"]})
                svc.proxy.list().update()  # You have to update proxy.list() to promote product to Staging APIcast
        elif proxy_params:
            svc.proxy.update(params=staging_gateway.get_proxy_settings(svc, proxy_params))
        staging_gateway.register_service(svc)

        for hook in _select_hooks("on_service_create", hooks):
            hook(svc)

        return svc

    return _custom_service


@pytest.fixture(scope="module")
def custom_backend(threescale, request, testconfig, private_base_url):
    """
    Parametrized custom Backend
    Args:
        :param name: name of backend
        :param endpoint: endpoint of backend
    """

    def _custom_backend(name="backend", endpoint=None, autoclean=True, hooks=None):
        if endpoint is None:
            endpoint = private_base_url()

        params = {"name": randomize(name), "private_endpoint": endpoint}

        for hook in _select_hooks("before_backend", hooks):
            hook(params)

        backend = threescale.backends.create(params=params)

        if autoclean and not testconfig["skip_cleanup"]:
            def finalizer():
                for hook in _select_hooks("on_backend_delete", hooks):
                    try:
                        hook(backend)
                    finally:
                        pass
                backend.delete()
            request.addfinalizer(finalizer)

        for hook in _select_hooks("on_backend_create", hooks):
            hook(backend)

        return backend

    return _custom_backend
