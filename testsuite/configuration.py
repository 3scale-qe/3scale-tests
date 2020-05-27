"""Module responsible for processing configuration"""
from dynaconf import settings

from testsuite.certificates import CertificateManager, CFSSLCertificate, TmpCertificateStore
from testsuite.openshift.client import OpenShiftClient
from testsuite.requirements import ThreeScaleAuthDetails, OpenshiftRequirement, CFSSLRequirement


# pylint: disable=too-many-instance-attributes
class CommonConfiguration(ThreeScaleAuthDetails, OpenshiftRequirement, CFSSLRequirement):
    """Class containing configuration of a testsuite which can be passed to other libraries"""

    def __init__(self) -> None:
        self._certificate = None
        self._store = None
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
    def certificate(self):
        if not self._certificate:
            self._certificate = CFSSLCertificate(host=settings["cfssl"]["host"],
                                                 port=settings["cfssl"]["port"])
        return self._certificate

    @property
    def certificate_store(self):
        if not self._store:
            self._store = TmpCertificateStore()
        return self._store

    @property
    def manager(self):
        if not self._manager:
            self._manager = CertificateManager(self.certificate, self.certificate_store)
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
