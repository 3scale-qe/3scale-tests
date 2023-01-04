"""
Conftest for performance tests
"""
import asyncio
import os
from concurrent.futures.thread import ThreadPoolExecutor
from pathlib import Path
from weakget import weakget

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
def shared_template(testconfig, number_of_agents):
    """Shared template for hyperfoil test, to set up agents
    By default is used configuration of agents set per test file, this can be overridden in configuration files.
    Default value is set to one agent.
    """
    if weakget(testconfig)["hyperfoil"]["shared_template"] % False:
        shared_template = testconfig.get('hyperfoil', {}).get('shared_template', {}).to_dict()
    else:
        shared_template: dict = {'agents': {}}
        for i in range(1, number_of_agents + 1):
            agent = {'host': 'localhost', 'port': 22, 'stop': True}
            shared_template['agents'][f'agent-{i}'] = agent

    return shared_template


@pytest.fixture(scope="module")
def event_loop():
    """Event loop for use in performance tests"""
    with ThreadPoolExecutor() as pool:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.set_default_executor(pool)
        yield loop
        loop.close()


@pytest.fixture(scope='module')
async def applications(services, custom_application, lifecycle_hooks, number_of_apps, event_loop):
    """Create multiple application for each service"""

    def _create_apps(svc):
        plan = svc.app_plans.list()[0]
        return custom_application(rawobj.Application(randomize("App"), plan), hooks=lifecycle_hooks)

    return await asyncio.gather(
         *(event_loop.run_in_executor(None, _create_apps, svc) for _ in range(number_of_apps) for svc in services)
    )


# pylint: disable=too-many-arguments
@pytest.fixture(scope='module')
async def services(request, custom_backend, custom_service, custom_app_plan, number_of_products, event_loop,
                   number_of_backends, service_proxy_settings, service_settings, private_base_url, lifecycle_hooks):
    """Create multiple services with multiple backends"""

    def _create_services():
        backends_mapping = {}
        for j in range(number_of_backends):
            backends_mapping[f"/{j}"] = custom_backend(endpoint=private_base_url("httpbin_go"))
        service_settings.update({"name": blame(request, randomize("perf"))})
        svc = custom_service(service_settings, service_proxy_settings, backends_mapping, hooks=lifecycle_hooks)
        custom_app_plan(rawobj.ApplicationPlan(randomize("AppPlan")), svc)
        return svc

    return await asyncio.gather(
        *(event_loop.run_in_executor(None, _create_services) for _ in range(number_of_products))
    )


@pytest.fixture(scope='module')
def promoted_services(services, production_gateway):
    """Promotes service and reloads production gateway"""
    for svc in services:
        version = svc.proxy.list().configs.latest()['version']
        svc.proxy.list().promote(version=version)
    production_gateway.reload()
    return services


@pytest.fixture(scope="module")
def prod_client(request):
    """Production client for performance tests omitting unecessary arguments.
    Client don't handle with default product which causes errors in performance tests.
    """
    def _client(app):
        client = app.api_client(endpoint="endpoint")
        request.addfinalizer(client.close)
        return client
    return _client
