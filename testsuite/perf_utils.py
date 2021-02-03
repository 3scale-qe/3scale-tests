"""
This file contains methods that are used in performance testing
"""
import os
from urllib.parse import urlparse

import yaml
from hyperfoil.factories import HyperfoilFactory, Benchmark

from testsuite import ROOT_DIR


def _load_benchmark(filename):
    """Loads benchmark"""
    with open(filename) as file:
        benchmark = Benchmark(yaml.load(file, Loader=yaml.Loader))
    return benchmark


def authority(url):
    """Returns hyperfoil authority format of URL <hostname>:<port> from given URL."""
    parsed_url = urlparse(url)
    return f"{parsed_url.hostname}:{parsed_url.port}"


class HyperfoilUtils:
    """
        Setup class for hyperfoil test.
        Also wrapper of Hyperfoil-python-client.
    """
    message_1kb = os.path.join(ROOT_DIR, 'testsuite/resources/performance/files/message_1kb.txt')

    def __init__(self, hyperfoil_client, template_filename):
        self.hyperfoil_client = hyperfoil_client
        self.factory = HyperfoilFactory(hyperfoil_client)
        self.benchmark = _load_benchmark(template_filename)

    def finalizer(self):
        """Hyporfoil factory opens a lot of file streams, we need to ensure that they are closed."""
        self.factory.close()

    def add_hosts(self, services, shared_connections: int, **kwargs):
        """Adds hosts of all applications to the benchmark"""
        for svc in services:
            url = svc.proxy.list()['endpoint']
            self.benchmark.add_host(url, shared_connections, **kwargs)

    def add_host(self, url: str, shared_connections: int, **kwargs):
        """Adds specific url host to the benchmark"""
        self.benchmark.add_host(url, shared_connections, **kwargs)

    def add_file(self, path):
        """Adds file to the benchmark"""
        filename = os.path.basename(path)
        self.factory.file(filename, open(path, 'r'))

    def generate_random_file(self, filename: str, size: int):
        """Generates and adds file with such filename and size to the benchmark"""
        self.factory.generate_random_file(filename, size)

    def generate_random_files(self, files: dict):
        """Generates and adds files to the benchmark"""
        for filename, size in files.items():
            self.factory.generate_random_file(filename, size)

    def add_user_key_auth(self, applications, filename):
        """
        Adds csv file to the benchmark with following columns of rows
        [authority url, auth user key, user key]
        :param applications: list of 3scale applications
        :param filename: name of csv file
        """
        rows = []
        for application in applications:
            url = authority(application.service.proxy.list()['endpoint'])
            auth_user_key = application.service.proxy.list()['auth_user_key']
            user_key = application['user_key']
            rows.append([url, auth_user_key, user_key])
        self.factory.csv_data(filename, rows)

    def add_oidc_auth(self, rhsso_service_info, applications, filename):
        """
        Adds csv file to the benchmark with following columns of a row:
        [authority url, access_token]
        :param rhsso_service_info: rhsso service info fixture
        :param applications: list of 3scale applications
        :param filename: name of csv file
        """
        rows = []
        for application in applications:
            url = authority(application.service.proxy.list()['endpoint'])
            token = rhsso_service_info.access_token(application)
            rows.append([url, token])
        self.factory.csv_data(filename, rows)

    def add_token_creation_data(self, rhsso_service_info, applications, filename):
        """
        Adds csv file with data for access token creation. Each row consits of following columns:
        [authority url, rhsso url, rhsso path, body for token creation]
        :param rhsso_service_info: rhsso service info fixture
        :param applications: list of 3scale applications
        :param filename: name of csv file
        :return:
        """
        rows = []
        token_url = urlparse(rhsso_service_info.token_url())
        token_port = 80 if token_url.scheme == 'http' else 443
        for application in applications:
            url = authority(application.service.proxy.list()['endpoint'])
            rows.append([url, f"{token_url.hostname}:{token_port}",
                         token_url.path, rhsso_service_info.body_for_token_creation(application)])
        self.factory.csv_data(filename, rows)

    def update_benchmark(self, benchmark):
        """Updates benchmark"""
        self.benchmark.update(benchmark=benchmark)

    def add_shared_template(self, shared_template):
        """Updates benchmark with shared template"""
        self.benchmark.update(shared_template)

    def create_benchmark(self):
        """Creates benchmark"""
        benchmark = self.benchmark.create()
        return self.factory.benchmark(benchmark).create()
