"""Module responsible for processing configuration"""
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
        return settings["threescale"]["gateway"]["template"]

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
        project_name = settings["openshift"]["projects"][project]["name"]

        try:
            server = settings["openshift"]["servers"][server]
        except KeyError:
            server = {}

        return OpenShiftClient(project_name=project_name,
                               server_url=server.get("server_url", None),
                               token=server.get("token", None))
