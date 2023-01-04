"""
    Smoke test that will create 3scale objects for performance testing.
    Fill necessary data to benchmark template.
    Run the test and assert results.
    This test shows usage how to write test where 3scale product is secured with user key.
"""
import asyncio
import os

import backoff
import pytest

from testsuite import rawobj
from testsuite.perf_utils import HyperfoilUtils

# Maximal runtime of test (need to cover all performance stages)
MAX_RUN_TIME = 5 * 60

pytestmark = [pytest.mark.performance]


@pytest.fixture(scope='module')
def number_of_products():
    """Number of created services (products)"""
    return 1


@pytest.fixture(scope='module')
def number_of_backends():
    """Number of created backends for single service (product)"""
    return 10


@pytest.fixture(scope='module')
def number_of_apps():
    """Number of created application for single service (product)"""
    return 1


@pytest.fixture(scope='module')
def create_mapping_rules():
    """
    Returns function that will be run for each backend usage
    """
    def _create(i, be_usage):
        metric = be_usage.backend.metrics.list()[0]
        be_usage.backend.mapping_rules.create(rawobj.Mapping(metric, f"/anything/{i}"))
        be_usage.backend.mapping_rules.create(rawobj.Mapping(metric, f"/anything/{i}", "POST"))
    return _create


@pytest.fixture(scope='module')
async def services(services, create_mapping_rules, event_loop):
    """
    Removes default mapping rule of each product.
    For each backend creates 20 mapping rules
    """
    for svc in services:
        proxy = svc.proxy.list()
        proxy.mapping_rules.delete(proxy.mapping_rules.list()[0]["id"])
    for svc in services:
        proxy = svc.proxy.list()
        futures = []
        for be_usage in svc.backend_usages.list():
            futures += [
                event_loop.run_in_executor(None, create_mapping_rules, i, be_usage)
                for i in range(10)]
        await asyncio.gather(*futures)
        proxy.deploy()
    return services


@pytest.fixture(scope='module')
def template(root_path):
    """Path to template"""
    return os.path.join(root_path, 'smoke/templates/template_user_key_query.hf.yaml')


@pytest.fixture(scope='module')
def hyperfoil_utils(hyperfoil_client, template, request):
    """Init of hyperfoil utils"""
    utils = HyperfoilUtils(hyperfoil_client, template)
    request.addfinalizer(utils.finalizer)
    return utils


@pytest.fixture(scope='module')
def setup_benchmark(hyperfoil_utils, applications, shared_template, promoted_services):
    """Setup of benchmark. It will add necessary host connections, csv data and files."""
    hyperfoil_utils.add_hosts(promoted_services, shared_connections=300)
    hyperfoil_utils.add_user_key_auth(applications, 'auth_user_key.csv')
    hyperfoil_utils.add_file(HyperfoilUtils.message_1kb)
    hyperfoil_utils.add_shared_template(shared_template)
    return hyperfoil_utils


@backoff.on_predicate(backoff.constant, lambda x: not x.is_finished(), interval=5, max_time=MAX_RUN_TIME)
def wait_run(run):
    """Waits for the run to end"""
    return run.reload()


def test_smoke_user_key(applications, prod_client,  setup_benchmark):
    """
        Test checks that application is setup correctly.
        Runs the created benchmark.
        Asserts it was successful.
    """
    for app in applications:
        client = prod_client(app)
        assert client.get("/0/anything/0").status_code == 200
        assert client.post("/0/anything/0").status_code == 200

    benchmark = setup_benchmark.create_benchmark()
    run = benchmark.start()

    run = wait_run(run)

    stats = run.all_stats()

    assert stats
    assert stats.get('info', {}).get('errors') == []
    assert stats.get('failures') == []
    assert stats.get('stats', []) != []
    assert len(stats.get('stats', [])) == 3
