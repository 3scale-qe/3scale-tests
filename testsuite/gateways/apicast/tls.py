"""Apicast with TLS certificates configured"""
import logging
from datetime import datetime
from typing import Optional

from threescale_api.resources import Application, Service

from testsuite.openshift.objects import Routes, SecretKinds
from . import AbstractApicast, OpenshiftApicast
from .selfmanaged import SelfManagedApicast
from .. import new_gateway
from ... import settings
from ...capabilities import Capability
from ...certificates import Certificate
from ...openshift.env import Properties

LOGGER = logging.getLogger(__name__)


class TLSApicast(AbstractApicast):
    """Apicast with TLS enabled, works for all subclasses of OpenshiftApicast (so both Template and Operator one)"""

    CAPABILITIES = {Capability.APICAST,
                    Capability.CUSTOM_ENVIRONMENT,
                    Capability.PRODUCTION_GATEWAY,
                    Capability.LOGS,
                    Capability.JAEGER}

    # pylint: disable=too-many-arguments
    def __init__(self, name, staging, superdomain, server_authority, manager, generate_name=False) -> None:
        super().__init__()
        # We expect that the SelfManagedApicast returns subclass of OpenshiftApicast,
        # which is for now true, but it is not ensured
        self.gateway: OpenshiftApicast = new_gateway({}, kind=SelfManagedApicast, staging=staging,  # type: ignore
                                                     settings_=settings["threescale"]["gateway"],
                                                     name=name, randomize_name=generate_name)
        # Ugly monkey-patching of a method
        self.gateway.add_route = self.add_route  # type: ignore
        self.secret_name = self.gateway.deployment.name
        self.superdomain = superdomain
        self.server_authority = server_authority
        self.manager = manager

    @property
    def _hostname(self):
        """Return wildcard hostname for certificates"""
        return f"*.{self.superdomain}"

    @property
    def server_certificate(self) -> Certificate:
        """Returns server certificate currently in-use"""
        return self.manager.get_or_create("server",
                                          self._hostname,
                                          hosts=[self._hostname],
                                          certificate_authority=self.server_authority)

    def on_application_create(self, application: Application):
        application.api_client_verify = self.server_authority.files["certificate"]

    def before_service(self, service_params: dict) -> dict:
        return self.gateway.before_service(service_params)

    def before_proxy(self, service: Service, proxy_params: dict):
        return self.gateway.before_proxy(service, proxy_params)

    def on_service_delete(self, service: Service):
        self.gateway.on_service_delete(service)

    def add_route(self, name, kind=Routes.Types.PASSTHROUGH):
        """Adds new route for this APIcast"""
        hostname = f"{name}.{self.superdomain}"
        result = self.openshift.routes.create(name, kind, hostname=hostname,
                                              service=self.deployment.name, port="httpsproxy")
        # pylint: disable=protected-access
        self.gateway._routes.append(name)
        return result

    def create(self):
        super().create()
        self.gateway.create()

        LOGGER.debug('Creating tls secret "%s"...', self.secret_name)
        self.openshift.secrets.create(name=self.secret_name, kind=SecretKinds.TLS, certificate=self.server_certificate)

        self.gateway.setup_tls(self.secret_name, 8443)

    def destroy(self):
        super().destroy()
        self.gateway.destroy()

        LOGGER.debug('Deleting secret "%s"', self.secret_name)
        self.openshift.delete("secret", self.secret_name)

        self.server_certificate.delete_files()

    @property
    def environ(self) -> Properties:
        return self.gateway.environ

    def reload(self):
        self.gateway.reload()

    def get_logs(self, since_time: Optional[datetime] = None) -> str:
        return self.gateway.get_logs(since_time)

    def __getattr__(self, item):
        if hasattr(self.gateway, item):
            return getattr(self.gateway, item)
        raise AttributeError(f"{self.__class__.__name__} object has no attribute {item}")
