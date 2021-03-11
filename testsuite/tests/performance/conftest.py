"""
Conftest for performance tests
"""
import asyncio
import os
from concurrent.futures.thread import ThreadPoolExecutor
from pathlib import Path

import pytest

from hyperfoil import HyperfoilClient

from testsuite.perf_utils import HyperfoilUtils

from testsuite import rawobj
from testsuite.utils import randomize, blame


@pytest.fixture(scope='session')
def hyperfoil_client(testconfig):
    """Hyperfoil client"""
    client = HyperfoilClient(testconfig['hyperfoil']['url'])
    return client


@pytest.fixture(scope='session')
def root_path():
    """Root path for performance tests"""
    return Path(os.path.abspath(__file__)).parent


@pytest.fixture(scope='module')
def number_of_products():
    """Number of created services (products)"""
    return 1


@pytest.fixture(scope='module')
def number_of_backends():
    """Number of created backends for single service (product)"""
    return 1


@pytest.fixture(scope='module')
def number_of_apps():
    """Number of created application for single service (product)"""
    return 1


@pytest.fixture(scope='module')
def hyperfoil_utils(hyperfoil_client, template, request):
    """Init of hyperfoil utils"""
    utils = HyperfoilUtils(hyperfoil_client, template)
    request.addfinalizer(utils.finalizer)
    return utils


@pytest.fixture(scope='module')
def shared_template(testconfig):
    """Shared template for hyperfoil test"""
    shared_template = testconfig.get('hyperfoil', {}).get('shared_template', {})
    return shared_template.to_dict()


@pytest.fixture(scope='module')
def applications(services, custom_application, lifecycle_hooks, number_of_apps):
    """Create multiple application for each service"""

    def _create_apps(svc):
        plan = svc.app_plans.list()[0]
        return custom_application(rawobj.Application(randomize("App"), plan), hooks=lifecycle_hooks)

    loop = asyncio.get_event_loop()
    apps = []
    futures = []
    with ThreadPoolExecutor() as pool:
        for svc in services:
            futures += [
                loop.run_in_executor(pool, _create_apps, svc)
                for _ in range(number_of_apps)]
        apps = loop.run_until_complete(asyncio.gather(*futures))
    return apps


# pylint: disable=too-many-arguments
@pytest.fixture(scope='module')
def services(request, custom_backend, custom_service, custom_app_plan, number_of_products,
             number_of_backends, service_proxy_settings, service_settings, lifecycle_hooks):
    """Create multiple services with multiple backends"""

    def _create_services():
        backends_mapping = {}
        for j in range(number_of_backends):
            backends_mapping[f"/{j}"] = custom_backend()
        service_settings.update({"name": blame(request, randomize("perf"))})
        svc = custom_service(service_settings, service_proxy_settings, backends_mapping, hooks=lifecycle_hooks)
        custom_app_plan(rawobj.ApplicationPlan(randomize("AppPlan")), svc)
        return svc

    loop = asyncio.get_event_loop()
    services = []
    with ThreadPoolExecutor() as pool:
        futures = [
            loop.run_in_executor(pool, _create_services)
            for _ in range(number_of_products)]
        services = loop.run_until_complete(asyncio.gather(*futures))
    return services


@pytest.fixture(scope='module')
def promoted_services(services, production_gateway):
    """Promotes service and reloads production gateway"""
    for svc in services:
        version = svc.proxy.list().configs.latest()['version']
        svc.proxy.list().promote(version=version)
    production_gateway.reload()
    return services
