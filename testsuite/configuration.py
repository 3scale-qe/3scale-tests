"""Module responsible for processing configuration"""
import inspect
import os.path
from typing import Dict, Any, Mapping

from weakget import weakget
import importlib_resources as resources

from testsuite.capabilities import Singleton
from testsuite.certificates.cfssl.cli import CFSSLProviderCLI
from testsuite.certificates.stores import InMemoryCertificateStore

from testsuite.config import settings
from testsuite.openshift.client import OpenShiftClient
from testsuite.requirements import ThreeScaleAuthDetails, OpenshiftRequirement, CertificateManager, \
    CertificateManagerRequirement


# pylint: disable=too-many-instance-attributes
class CommonConfiguration(ThreeScaleAuthDetails, OpenshiftRequirement, CertificateManagerRequirement):
    """Class containing configuration of a testsuite which can be passed to other libraries"""

    def __init__(self) -> None:
        self._manager = None

    @property
    def token(self):
        return settings["threescale"]["admin"]["token"]

    @property
    def url(self):
        return settings["threescale"]["admin"]["url"]

    @property
    def gateway_template(self) -> str:
        """Template for Gateway"""
        template = settings["threescale"]["gateway"]["template"]
        if template.endswith(".yml") and template == os.path.basename(template):
            return resources.files("testsuite.resources").joinpath(template)
        return template

    @property
    def gateway_image(self) -> str:
        """Docker image for Gateway"""
        return settings["threescale"]["gateway"]["image"]

    @property
    def manager(self):
        if not self._manager:
            provider = CFSSLProviderCLI(binary=settings["cfssl"]["binary"])
            store = InMemoryCertificateStore()
            self._manager = CertificateManager(provider, provider, store)
        return self._manager

    @property
    def superdomain(self):
        """ThreeScale superdomain"""
        return settings["threescale"]["superdomain"]

    def openshift(self, server="default", project="threescale") -> OpenShiftClient:
        """Creates OpenShiftClient for project"""
        project_name = weakget(settings)["openshift"]["projects"][project]["name"] % project

        try:
            server = settings["openshift"]["servers"][server]
        except KeyError:
            server = {}

        return OpenShiftClient(project_name=project_name,
                               server_url=server.get("server_url", None),
                               token=server.get("token", None))


def call(method, **kwargs):
    """Calls method with only parameters it requires"""
    expected = inspect.signature(method).parameters.keys()
    return method(**{k: v for k, v in kwargs.items() if k in expected})


class SettingsParser(metaclass=Singleton):
    """
    Parses settings into objects
    """
    def __init__(self) -> None:
        super().__init__()
        self.kinds: Dict[str, Any] = {}

    def register_kind(self, provider, kind: str = None):
        """Register new Kind"""
        if inspect.isclass(provider):
            kind = provider.__name__
        self.kinds[kind] = provider  # type: ignore

    def process(self, kind, global_kwargs=None, **kwargs):
        """
        Processes the kwargs and returns instantiated class
        :param kind: Str representation or kind or a Class
        :param global_kwargs: Arguments that will be passed to every kind regardless of depth,
        used for parametrized kinds
        :param kwargs: Arguments to be processed
        :return: Instantiated class
        """
        global_kwargs = global_kwargs or {}
        if inspect.isclass(kind) or inspect.isfunction(kind):
            method = kind
        else:
            method = self.kinds[kind]

        # process dicts
        processed_kwargs = {**global_kwargs}
        for key, value in kwargs.items():
            if isinstance(value, Mapping) and "kind" in value:
                processed_kwargs[key] = self.process(**value, global_kwargs=global_kwargs)
            else:
                processed_kwargs[key] = value
        return call(method, **processed_kwargs)


SettingsParser().register_kind(provider=OpenShiftClient)
