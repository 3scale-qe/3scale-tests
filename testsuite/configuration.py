"""Module responsible for processing configuration"""
from dynaconf import settings

from testsuite.certificates import CertificateManager
from testsuite.certificates.cfssl import CFSSLCertificate
from testsuite.certificates.stores import TmpCertificateStore
from testsuite.openshift.client import OpenShiftClient
from testsuite.requirements import ThreeScaleAuthDetails, OpenshiftRequirement, CFSSLRequirement


# pylint: disable=too-many-instance-attributes
class CommonConfiguration(ThreeScaleAuthDetails, OpenshiftRequirement, CFSSLRequirement):
    """Class containing configuration of a testsuite which can be passed to other libraries"""

    def __init__(self) -> None:
        self._token = None
        self._master_token = None
        self._url = None
        self._master_url = None
        self._project = None
        self._certificate = None
        self._store = None
        self._manager = None
        self._superdomain = None

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
    def master_token(self):
        """Threescale master token"""
        if not self._master_token:
            self._master_token = self._load_master_token()
        return self._master_token

    @property
    def url(self):
        if not self._url:
            self._url = self._load_url()
        return self._url

    @property
    def master_url(self):
        """Threescale master url"""
        if not self._master_url:
            self._master_url = self._load_master_url()
        return self._master_url

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
        if not self._superdomain:
            self._superdomain = self.openshift().config_maps["system-environment"]["THREESCALE_SUPERDOMAIN"]
        return self._superdomain

    @staticmethod
    def _load_project():
        try:
            return settings["openshift"]["projects"]["threescale"]["name"]
        except KeyError:
            return settings["env_for_dynaconf"]

    def _load_token(self):
        # This part is trying to get the admin token, by default is saved in the
        # system-seed openshift secret
        token = settings.get("threescale", {}).get("admin", {}).get("token")
        if token:
            return token

        try:
            return self.openshift().secrets["system-seed"]["ADMIN_ACCESS_TOKEN"].decode("utf-8")
        except KeyError:
            Exception("(From Openshift) cannot get system-seed access token. Review your settings")

    def _load_master_token(self):
        # This part is trying to get the master token, by default is saved in the
        # system-seed openshift secret
        token = settings.get("threescale", {}).get("master", {}).get("token")
        if token:
            return token

        try:
            return self.openshift().secrets["system-seed"]["MASTER_ACCESS_TOKEN"].decode("utf-8")
        except KeyError:
            Exception("(From Openshift) cannot get system-seed master access token. Review your settings")

    def _load_url(self):
        # This is trying to get system default route. If not defined, is going to
        # search that on the openshift routes.
        url = settings.get("threescale", {}).get("admin", {}).get("url")
        if url:
            return url

        try:
            route = self.openshift().routes.for_service("system-provider")[0]
            return "https://" + route["spec"]["host"]
        except KeyError:
            Exception("(From Openshift) cannot get system default route. Review your settings")

    def _load_master_url(self):
        # This is trying to get system default route. If not defined, is going to
        # search that on the openshift routes.
        url = settings.get("threescale", {}).get("master", {}).get("url")
        if url:
            return url

        try:
            route = self.openshift().routes.for_service("system-master")[0]
            return "https://" + route["spec"]["host"]
        except KeyError:
            Exception("(From Openshift) cannot get system default route. Review your settings")

    def openshift(self, server="default", project="threescale") -> OpenShiftClient:
        """Creates OpenShiftClient for project"""
        try:
            project_name = settings["openshift"]["projects"][project]["name"]
        except KeyError:
            if project != "threescale":
                raise AttributeError("Project %s is not defined in configuration" % project)
            project_name = self.project

        try:
            server = settings["openshift"]["servers"][server]
        except KeyError:
            server = {}

        return OpenShiftClient(project_name=project_name,
                               server_url=server.get("server_url", None),
                               token=server.get("token", None))
