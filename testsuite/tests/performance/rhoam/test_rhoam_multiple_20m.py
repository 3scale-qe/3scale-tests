"""
    Performance test for managed services with multiple 3scale entities (products, backends,...)
"""
import asyncio
import os
from concurrent.futures.thread import ThreadPoolExecutor
from urllib.parse import urlparse

import backoff
import pytest

from testsuite import rawobj
from testsuite.rhsso.rhsso import OIDCClientAuthHook

MAX_RUN_TIME = 210 * 60
NUMBER_OF_BACKENDS = 10
NUMBER_OF_PRODUCTS = 10
NUMBER_OF_APPLICATIONS = 10
NUMBER_OF_MAPPING_RULES_PER_BACKEND = 10

PAYLOAD_FILES = {
    "payload_5KB.txt": 5 * 1042,
    "payload_20KB.txt": 20 * 1024,
    "payload_100KB.txt": 100 * 1024,
    "payload_500KB.txt": 500 * 1024,
    "payload_1MB.txt": 1024 * 1024,
    "payload_5MB.txt": 5 * 1024 * 1024,
}

pytestmark = [pytest.mark.performance]


@pytest.fixture(scope="module", autouse=True)
def rhsso_setup(lifecycle_hooks, rhsso_service_info):
    """Have application/service with RHSSO auth configured"""
    # , accessTokenLifespan=24*60
    lifecycle_hooks.append(OIDCClientAuthHook(rhsso_service_info))


@pytest.fixture(scope="module")
def number_of_products():
    """Number of created services (products)"""
    return NUMBER_OF_PRODUCTS


@pytest.fixture(scope="module")
def number_of_backends():
    """Number of created backends for single service (product)"""
    return NUMBER_OF_BACKENDS


@pytest.fixture(scope="module")
def number_of_apps():
    """Number of created application for single service (product)"""
    return NUMBER_OF_APPLICATIONS


@pytest.fixture(scope="module")
def number_of_agents():
    """Number of Hyperfoil agents to be spawned"""
    return 2


@pytest.fixture(scope="module")
def create_mapping_rules():
    """
    Returns function that will be run for each backend usage
    """

    def _create(i, be_usage):
        metric = be_usage.backend.metrics.list()[0]
        be_usage.backend.mapping_rules.create(rawobj.Mapping(metric, f"/anything/{i}"))
        be_usage.backend.mapping_rules.create(rawobj.Mapping(metric, f"/anything/{i}", "POST"))

    return _create


@pytest.fixture(scope="module")
def services(services, create_mapping_rules):
    """
    Removes default mapping rule of each product.
    For each backend creates 10 mapping rules
    """
    loop = asyncio.get_event_loop()
    for svc in services:
        proxy = svc.proxy.list()
        proxy.mapping_rules.delete(proxy.mapping_rules.list()[0]["id"])
    with ThreadPoolExecutor() as pool:
        for svc in services:
            proxy = svc.proxy.list()
            futures = []
            for be_usage in svc.backend_usages.list():
                futures += [
                    loop.run_in_executor(pool, create_mapping_rules, i, be_usage)
                    for i in range(NUMBER_OF_MAPPING_RULES_PER_BACKEND)
                ]
            loop.run_until_complete(asyncio.gather(*futures))
            proxy.update()
    return services


@pytest.fixture(scope="module")
def template(root_path):
    """Path to template"""
    return os.path.join(root_path, "rhoam/templates/template_multiple_oidc_20m.hf.yaml")


@pytest.fixture(scope="module")
def setup_benchmark(hyperfoil_utils, rhsso_service_info, applications, shared_template, promoted_services):
    """Setup of benchmark. It will add necessary host connections, csv data and files."""
    hyperfoil_utils.add_hosts(promoted_services, shared_connections=1000)
    hyperfoil_utils.add_host(
        urlparse(rhsso_service_info.rhsso.server_url)._replace(path="").geturl(), shared_connections=500
    )
    hyperfoil_utils.add_oidc_auth(rhsso_service_info, applications, "auth_oidc.csv")
    hyperfoil_utils.generate_random_files(PAYLOAD_FILES)
    hyperfoil_utils.add_shared_template(shared_template)
    return hyperfoil_utils


@backoff.on_predicate(backoff.constant, lambda x: not x.is_finished(), interval=5, max_time=MAX_RUN_TIME)
def wait_run(run):
    """Waits for the run to end"""
    return run.reload()


def test_smoke_user_key(applications, setup_benchmark):
    """
    Test checks that application is setup correctly.
    Runs the created benchmark.
    Asserts it was successful.
    """
    for app in applications:
        assert app.api_client(endpoint="endpoint").get("/0/anything/0").status_code == 200
        assert app.api_client(endpoint="endpoint").post("/0/anything/0").status_code == 200

    benchmark = setup_benchmark.create_benchmark()
    run = benchmark.start()

    run = wait_run(run)

    stats = run.all_stats()

    assert stats
    assert stats.get("info", {}).get("errors") == []
    assert stats.get("failures") == []
    assert stats.get("stats", []) != []
    # The following assert depends the benchmark used for smoke/template_multiple_oidc_20m.hf.yaml it would be 23
    # assert len(stats.get('stats', [])) == 3
