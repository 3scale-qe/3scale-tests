"""Module responsible for processing configuration"""
from openshift import OpenShiftPythonException
from dynaconf import settings

from testsuite.certificates import CertificateManager, CFSSLCertificate, TmpCertificateStore
from testsuite.openshift.client import OpenShiftClient
from testsuite.requirements import ThreeScaleAuthDetails, OpenshiftRequirement, CFSSLRequirement


# pylint: disable=too-many-instance-attributes
class CommonConfiguration(ThreeScaleAuthDetails, OpenshiftRequirement, CFSSLRequirement):
    """Class containing configuration of a testsuite which can be passed to other libraries"""

    def __init__(self) -> None:
        self._servers = settings["openshift"]["servers"]
        self._projects = settings["openshift"]["projects"]
        self._token = None
        self._url = None
        self._project = None
        self._certificate = None
        self._store = None
        self._manager = None

    @property
    def project(self):
        """ThreeScale project name"""
        if not self._project:
            self._project = self._load_project()
        return self._project

    @property
    def token(self):
        if not self._token:
            self._token = self._load_token()
        return self._token

    @property
    def url(self):
        if not self._url:
            self._url = self._load_url()
        return self._url

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

    @staticmethod
    def _load_project():
        try:
            return settings["openshift"]["projects"]["threescale"]["name"]
        except KeyError:
            return settings["env_for_dynaconf"]

    def _load_token(self):
        try:
            try:
                return settings["threescale"]["admin"]["token"]
            except KeyError:
                return self.openshift().secrets["system-seed"]["ADMIN_ACCESS_TOKEN"].decode("utf-8")
        except OpenShiftPythonException as err:
            oc_error = err.result.as_dict()["actions"][0]["err"]
            raise Exception(f"(From Openshift) {oc_error}")

    def _load_url(self):
        try:
            try:
                return settings["threescale"]["admin"]["url"]
            except KeyError:
                route = self.openshift().routes.for_service("system-provider")[0]
                return "https://" + route["spec"]["host"]
        except OpenShiftPythonException as err:
            oc_error = err.result.as_dict()["actions"][0]["err"]
            raise Exception(f"(From Openshift) {oc_error}")

    def openshift(self, server="default", project="threescale") -> OpenShiftClient:
        """Creates OpenShiftClient for project"""
        if server not in self._servers:
            raise AttributeError("Server %s is not defined in configuration" % server)
        try:
            project_name = self._projects[project]["name"]
        except KeyError:
            if project != "threescale":
                raise AttributeError("Project %s is not defined in configuration" % project)
            project_name = self.project

        server = self._servers[server]
        return OpenShiftClient(project_name=project_name,
                               server_url=server.get("server_url", None),
                               token=server.get("token", None))
