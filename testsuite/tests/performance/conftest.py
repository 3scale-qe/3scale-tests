"""
Conftest for performance tests
"""
import os
from pathlib import Path

import pytest
from hyperfoil import HyperfoilClient

from testsuite.perf_utils import HyperfoilUtils


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
def applications(application):
    """List of applications"""
    return [application]


@pytest.fixture(scope='module')
def hyperfoil_utils(hyperfoil_client, applications, template, request):
    """Init of hyperfoil utils"""
    utils = HyperfoilUtils(hyperfoil_client, applications, template)
    request.addfinalizer(utils.finalizer)
    return utils


@pytest.fixture(scope='module')
def shared_template(testconfig):
    """Shared template for hyperfoil test"""
    shared_template = testconfig.get('hyperfoil', {}).get('shared_template', {})
    return shared_template.to_dict()
