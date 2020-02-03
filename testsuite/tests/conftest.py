"top-level conftest"
import os
import time

import pytest

import urllib3
from dynaconf import settings
from threescale_api import client

from testsuite import rawobj
from testsuite.gateways import GATEWAY_CLASSES
from testsuite.openshift.client import OpenShiftClient
from testsuite.utils import randomize
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


def pytest_addoption(parser):
    """Add option to include disruptive tests in testrun"""
    parser.addoption(
        "--disruptive", action="store_true", default=False, help="Run also disruptive tests (default: False)")


def pytest_runtest_setup(item):
    """Exclude disruptive tests by default, require explicit option"""

    marks = [i.name for i in item.iter_markers()]
    if "disruptive" in marks and not item.config.getoption("--disruptive"):
        pytest.skip("Excluding disruptive tests")


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


@pytest.fixture()
def redeploy_production_gateway(openshift):
    "Redeploys production gateway"
    def _func():
        openshift().rollout("dc/apicast-production")
    return _func


@pytest.fixture(scope="session")
def testconfig():
    "testsuite configuration"
    return settings


@pytest.fixture(scope="session")
def threescale(testconfig, openshift):
    "Threescale client"

    try:
        token = testconfig["threescale"]["admin"]["token"]
    except KeyError:
        token = openshift().secrets["system-seed"]["ADMIN_ACCESS_TOKEN"]

    try:
        url = testconfig["threescale"]["admin"]["url"]
    except KeyError:
        route = openshift().routes.for_service("system-provider")[0]
        url = "https://" + route["spec"]["host"]

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


@pytest.fixture(scope="module")
def staging_gateway(request, testconfig):
    """Staging gateway"""
    configuration = testconfig["threescale"]["gateway"]["configuration"]
    gateway = GATEWAY_CLASSES["staging"](configuration=configuration, openshift=openshift, staging=False)
    gateway.create()

    request.addfinalizer(gateway.destroy)
    return gateway


@pytest.fixture(scope="module")
def production_gateway(request, testconfig):
    """Production gateway"""
    configuration = testconfig["threescale"]["gateway"]["configuration"]
    gateway = GATEWAY_CLASSES["production"]
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
def service_proxy_settings(backend):
    "dict of proxy settings to be used when service created"
    return rawobj.Proxy(backend())


@pytest.fixture(scope="module")
def backend(testconfig):
    """URL to API backend.

    This is callable fixture with parameter `kind`.
    `kind="primary"` returns backend to be used primarily/by default.

    Args:
        :param kind: Desired type of backend; possible values 'primary' (default), 'httpbin', 'echo-api'"""

    def _backend(kind="primary"):
        return testconfig["threescale"]["service"]["backends"][kind]

    return _backend


@pytest.fixture(scope="module")
def service_settings():
    "dict of service settings to be used when service created"
    return {"name": randomize("service")}


@pytest.fixture(scope="module")
def service(custom_service, service_settings, service_proxy_settings):
    "Preconfigured service with backend defined existing over whole testsing session"
    return custom_service(service_settings, service_proxy_settings)


@pytest.fixture(scope="module")
def application(service, custom_application, custom_app_plan):
    "application bound to the account and service existing over whole testing session"
    plan = custom_app_plan(rawobj.ApplicationPlan(randomize("AppPlan")), service)
    return custom_application(rawobj.Application(randomize("App"), plan))


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

    def _custom_app_plan(params, service=None):
        if service is None:
            service = custom_service({"name": randomize("service")}, service_proxy_settings)
        plan = service.app_plans.create(params=params)
        plans.append(plan)
        return plan

    if not testconfig["skip_cleanup"]:
        request.addfinalizer(lambda: [item.delete() for item in plans])

    return _custom_app_plan


# custom_app_plan dependency is needed to ensure cleanup in correct order
@pytest.fixture(scope="module")
def custom_application(account, custom_app_plan, request, testconfig):  # pylint: disable=unused-argument
    """Parametrized custom Application

    Args:
        :param params: dict for remote call, rawobj.Application should be used

    (Typical) Usage:
        plan = custom_app_plan(rawobj.ApplicationPlan("CustomPlan"), service)
        app = custom_application(rawobj.Application("CustomApp", plan))
    """
    apps = []

    def _custom_application(params):
        app = account.applications.create(params=params)

        apps.append(app)

        app.api_client_verify = testconfig["ssl_verify"]

        return app

    if not testconfig["skip_cleanup"]:
        request.addfinalizer(lambda: [item.delete() for item in apps])

    return _custom_application


@pytest.fixture(scope="module")
def custom_service(threescale, request, testconfig, staging_gateway):
    """Parametrized custom Service

    Args:
        :param params: dict for remote call
        :param proxy_params: dict of proxy options for remote call, rawobj.Proxy should be used"""
    svcs = []

    def _custom_service(params, proxy_params):
        svc = threescale.services.create(params=staging_gateway.get_service_settings(params))
        svcs.append(svc)

        # Due to asynchronous nature of 3scale the proxy is not always ready immediately,
        # this is not necessarily bug of 3scale but we need to compensate for it regardless
        time.sleep(1)

        svc.proxy.update(params=staging_gateway.get_proxy_settings(svc, proxy_params))
        staging_gateway.register_service(svc)

        return svc

    if not testconfig["skip_cleanup"]:
        def _cleanup():
            for svc in svcs:
                staging_gateway.unregister_service(svc)
                svc.delete()
        request.addfinalizer(_cleanup)

    return _custom_service
