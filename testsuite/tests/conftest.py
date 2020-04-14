"top-level conftest"

import logging
import time

import pytest
import threescale_api

import urllib3

from dynaconf import settings
from threescale_api import client
import testsuite.gateways as gateways

from testsuite import rawobj, CONFIGURATION
from testsuite.utils import retry_for_session, blame, blame_desc
from testsuite.rhsso.rhsso import RHSSOServiceConfiguration, RHSSO, add_realm_management_role, create_rhsso_user

if settings["ignore_insecure_ssl_warning"]:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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
                if capability not in gateways.capabilities:
                    pytest.skip(f"Skipping test because current gateway doesn't have capability {capability}")


# pylint: disable=unused-argument
def pytest_report_header(config):
    """Add basic details about testsuite configuration"""

    environment = settings["env_for_dynaconf"]
    openshift = settings["openshift"]["servers"]["default"]["server_url"]

    project = CONFIGURATION.project
    threescale = CONFIGURATION.url
    token = CONFIGURATION.token

    return [
        "",
        f"testsuite: environment = {environment}",
        f"testsuite: openshift = {openshift}",
        f"testsuite: project = {project}",
        f"testsuite: threescale = {threescale}",
        f"testsuite: threescale_token = {token}",
        ""]


@pytest.fixture(scope="module")
def logger(request):
    """Preconfigured python logger for fixtures and tests"""

    return logging.getLogger(request.node.name)


@pytest.fixture(scope="session")
def openshift(configuration):
    "OpenShift client generator"
    return configuration.openshift


@pytest.fixture(scope="module")
def prod_client(production_gateway, application):
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
def configuration():
    "CommonConfiguration instance"
    return CONFIGURATION


@pytest.fixture(scope="session")
def testconfig():
    "testsuite configuration"
    return settings


@pytest.fixture(scope="session")
def threescale(configuration, testconfig):
    "Threescale client"
    verify = testconfig["ssl_verify"]
    return client.ThreeScaleClient(configuration.url, configuration.token, ssl_verify=verify)


@pytest.fixture(scope="session")
def account(threescale, request, testconfig):
    "Preconfigured account existing over whole testing session"
    name = blame(request, "id")
    account = dict(name=name, username=name, org_name=name,
                   email=f"{name}@anything.invalid")
    account = threescale.accounts.create(params=account)

    if not testconfig["skip_cleanup"]:
        request.addfinalizer(account.delete)

    return account


@pytest.fixture(scope="session")
def staging_gateway(request, testconfig, configuration):
    """Staging gateway"""
    options = gateways.configuration.options(staging=True,
                                             settings_block=testconfig["threescale"]["gateway"]["configuration"],
                                             configuration=configuration)
    gateway = gateways.configuration.staging(options)
    gateway.create()

    request.addfinalizer(gateway.destroy)
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
    realm = rhsso.create_realm(blame(request, "realm"))

    if not testconfig["skip_cleanup"]:
        request.addfinalizer(realm.delete)

    client = realm.clients.create(id=blame(request, "client"), serviceAccountsEnabled=True, standardFlowEnabled=False)

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
def service_settings(request):
    "dict of service settings to be used when service created"
    return {"name": blame(request, "svc")}


@pytest.fixture(scope="module")
def lifecycle_hooks(staging_gateway, production_gateway):
    """List of objects with hooks into app/svc creation and deletion

    Hooks should implement methods defined and documented in testsuite.lifecycle_hook.LifecycleHook
    or should inherit from that class"""

    return [staging_gateway, production_gateway]


@pytest.fixture(scope="module")
def service(backends_mapping, custom_service, service_settings, service_proxy_settings, lifecycle_hooks):
    "Preconfigured service with backend defined existing over whole testsing session"
    return custom_service(service_settings, service_proxy_settings, backends_mapping, hooks=lifecycle_hooks)


@pytest.fixture(scope="module")
def application(service, custom_application, custom_app_plan, lifecycle_hooks, request):
    "application bound to the account and service existing over whole testing session"
    plan = custom_app_plan(rawobj.ApplicationPlan(blame(request, "aplan")), service)
    return custom_application(rawobj.Application(blame(request, "app"), plan), hooks=lifecycle_hooks)


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
            service = custom_service({"name": blame(request, "svc")}, service_proxy_settings)
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
def custom_service(threescale, request, testconfig, staging_gateway, logger):
    """Parametrized custom Service

    Args:
        :param params: dict for remote call
        :param proxy_params: dict of proxy options for remote call, rawobj.Proxy should be used
        :param hooks: List of objects implementing necessary methods from testsuite.lifecycle_hook.LifecycleHook"""

    # pylint: disable=too-many-arguments
    def _custom_service(params, proxy_params=None, backends=None, autoclean=True, hooks=None, annotate=True):
        params = params.copy()
        for hook in _select_hooks("before_service", hooks):
            params = hook(params)

        if annotate:
            params["description"] = blame_desc(request, params.get("description"))

        svc = threescale.services.create(params=params)

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
                        implicit[0].delete()
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

            # You have to update proxy.list() to promote product to Staging APIcast
            svc.proxy.list().update(params=proxy_params)
        elif proxy_params:
            for hook in _select_hooks("before_proxy", hooks):
                proxy_params = hook(svc, proxy_params)

            svc.proxy.update(params=proxy_params)

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

    def _custom_backend(name="be", endpoint=None, autoclean=True, hooks=None):
        if endpoint is None:
            endpoint = private_base_url()

        params = {"name": blame(request, name), "private_endpoint": endpoint}

        for hook in _select_hooks("before_backend", hooks):
            hook(params)

        backend = threescale.backends.create(params=params)

        if autoclean and not testconfig["skip_cleanup"]:
            def finalizer():
                for hook in _select_hooks("on_backend_delete", hooks):
                    try:
                        hook(backend)
                    except Exception:  # pylint: disable=broad-except
                        pass
                backend.delete()
            request.addfinalizer(finalizer)

        for hook in _select_hooks("on_backend_create", hooks):
            hook(backend)

        return backend

    return _custom_backend
