"""Collection of gateways that are Apicast-based"""
import base64
import logging
from typing import Dict
from urllib.parse import urlparse

from threescale_api.resources import Service

from testsuite.certificates import (CertificateManager, CFSSLCertificate, TmpCertificateStore,
                                    CreateCertificateResponse, GetCertificateResponse)
from testsuite.gateways.gateways import AbstractApicast, Capability
from testsuite.openshift.client import OpenShiftClient
from testsuite.openshift.objects import Routes

# logging support should be rewritten
LOGGER = logging.getLogger(__name__)


class SystemApicast(AbstractApicast):
    """Apicast that is deployed with 3scale"""

    CAPABILITIES = [Capability.SAME_CLUSTER,
                    Capability.CUSTOM_ENVIRONMENT,
                    Capability.APICAST,
                    Capability.PRODUCTION_GATEWAY]

    def __init__(self, staging: bool, configuration, openshift):
        super().__init__(staging, configuration, openshift)
        if staging:
            self.deployment_name = configuration["staging_deployment"]
        else:
            self.deployment_name = configuration["production_deployment"]
        self.openshift: OpenShiftClient = openshift()

    def get_service_settings(self, service_settings: Dict) -> Dict:
        return service_settings

    def get_proxy_settings(self, service: Service, proxy_settings: Dict) -> Dict:
        return proxy_settings

    def set_env(self, name: str, value):
        self.openshift.environ(self.deployment_name)[name] = value

    def get_env(self, name: str):
        return self.openshift.environ(self.deployment_name)[name]

    def reload(self):
        self.openshift.rollout(f"dc/{self.deployment_name}")


class SelfManagedApicast(AbstractApicast):
    """Gateway for use with already deployed self-managed Apicast without ability to edit it"""

    CAPABILITIES = [Capability.APICAST]

    def __init__(self, staging: bool, configuration, openshift) -> None:
        super().__init__(staging, configuration, openshift)
        self.staging_endpoint = configuration["sandbox_endpoint"]
        self.production_endpoint = configuration["production_endpoint"]

        deployments = configuration["deployments"]
        if staging:
            self.deployment = deployments["staging"]
        else:
            self.deployment = deployments["production"]

        # Load openshift configuration
        self.project = configuration.get("project", "threescale")
        self.server = configuration.get("server", "default")
        self.openshift = openshift(server_name=self.server, project_name=self.project)

    def get_service_settings(self, service_settings: Dict) -> Dict:
        service_settings.update({
            "deployment_option": "self_managed"
        })
        return service_settings

    def get_proxy_settings(self, service: Service, proxy_settings: Dict) -> Dict:
        entity_id = service.entity_id
        proxy_settings.update({
            "sandbox_endpoint": self.staging_endpoint % entity_id,
            "endpoint": self.production_endpoint % entity_id
        })
        return proxy_settings

    def set_env(self, name: str, value):
        self.openshift.environ(self.deployment)[name] = value

    def get_env(self, name: str):
        return self.openshift.environ(self.deployment)[name]

    def reload(self):
        self.openshift.rollout(self.deployment)


class OperatorApicast(SelfManagedApicast):
    """Gateway for use with Apicast deployed by operator"""
    def __init__(self, staging: bool, configuration, openshift) -> None:
        super().__init__(staging, configuration, openshift)
        services = configuration["services"]
        self.service_staging = services["staging"]
        self.service_production = services["production"]

    def register_service(self, service: Service):
        entity_id = service.entity_id
        staging_url = urlparse(self.staging_endpoint % entity_id)
        prod_url = urlparse(self.production_endpoint % entity_id)
        self.openshift.routes.expose(name=f"{entity_id}-staging",
                                     service=self.service_staging, hostname=staging_url.hostname)
        self.openshift.routes.expose(name=f"{entity_id}-production",
                                     service=self.service_production, hostname=prod_url.hostname)

    def unregister_service(self, service: Service):
        del self.openshift.routes[f"{service.entity_id}-staging"]
        del self.openshift.routes[f"{service.entity_id}-production"]

    def set_env(self, name: str, value):
        raise NotImplementedError()

    def get_env(self, name: str):
        raise NotImplementedError()

    def reload(self):
        self.openshift.do_action("delete", ["pod", "--force",
                                            "--grace-period=0", "-l", f"deployment={self.deployment}"])
        # pylint: disable=protected-access
        self.openshift._wait_for_deployment(f"deployment/{self.deployment}")


class TemplateApicast(SelfManagedApicast):
    """Template-based Apicast Gateway."""

    def __init__(self, staging: bool, configuration, openshift) -> None:
        super().__init__(staging, configuration, openshift)
        self.openshift: OpenShiftClient = openshift()
        self.staging = staging
        self.template = configuration["template"]
        self.image = configuration["image"]
        self.service_name = self.deployment
        self.configuration_url_secret_name = f'{self.deployment}-config-url'

    def get_app_params(self, **kwargs):
        """Template envs for oc new-app."""
        params = {
            "APICAST_NAME": self.deployment,
            "AMP_APICAST_IMAGE": self.image,
            "DEPLOYMENT_ENVIRONMENT": "production",
            "CONFIGURATION_LOADER": "boot",
            "CONFIGURATION_CACHE": 300,
            "LOG_LEVEL": "debug",
            "CONFIGURATION_URL_SECRET": self.configuration_url_secret_name,
        }

        if self.staging:
            params.update({
                "CONFIGURATION_LOADER": "lazy",
                "DEPLOYMENT_ENVIRONMENT": "staging",
                "CONFIGURATION_CACHE": 0,
            })

        params.update(**kwargs)

        return params

    @property
    def _configuration_url(self):
        try:
            url = self.configuration["apicast-configuration-url-secret"]
        except KeyError:
            token = self.openshift.secrets["system-seed"]["ADMIN_ACCESS_TOKEN"].decode("utf-8")
            host = self.openshift.routes.for_service("system-provider")[0]["spec"]["host"]
            url = f"https://{token}@{host}"
        return url.encode("utf-8")

    def _get_configuration_url_secret_resource(self):
        config_url = base64.b64encode(self._configuration_url).decode("utf-8")
        return {
            "kind": "Secret",
            "apiVersion": "v1",
            "metadata": {
                "name": self.configuration_url_secret_name,
            },
            "data": {
                "password": config_url,
            },
            "type": "kubernetes.io/basic-auth"
        }

    def _create_configuration_url_secret(self):
        if self.configuration_url_secret_name not in self.openshift.secrets:
            LOGGER.debug('Secret "%s" does not exist. Creating...', self.configuration_url_secret_name)

            self.openshift.apply(self._get_configuration_url_secret_resource())

    def register_service(self, service: Service):
        entity_id = service.entity_id
        staging_url = urlparse(self.staging_endpoint % entity_id)
        prod_url = urlparse(self.production_endpoint % entity_id)
        self.openshift.routes.expose(name=f"{entity_id}-staging",
                                     service=self.service_name, hostname=staging_url.hostname)
        self.openshift.routes.expose(name=f"{entity_id}-production",
                                     service=self.service_name, hostname=prod_url.hostname)

    def unregister_service(self, service: Service):
        del self.openshift.routes[f"{service.entity_id}-staging"]
        del self.openshift.routes[f"{service.entity_id}-production"]

    def set_env(self, name: str, value):
        self.openshift.environ(self.deployment)[name] = value

    def get_env(self, name: str):
        return self.openshift.environ(self.deployment)[name]

    def create(self):
        LOGGER.debug('Deploying new template-based apicast "%s". Template params: "%s"',
                     self.deployment, self.get_app_params())

        self._create_configuration_url_secret()

        self.openshift.new_app(self.template, self.get_app_params())

        # pylint: disable=protected-access
        self.openshift._wait_for_deployment(self.deployment)

    def destroy(self):
        LOGGER.debug('Destroying template-based apicast "%s"...', self.deployment)

        LOGGER.debug('Deleting service "%s"', self.deployment)
        self.openshift.delete("service", self.deployment)

        LOGGER.debug('Deleting deploymentconfig "%s"', self.deployment)
        self.openshift.delete("deploymentconfig", self.deployment)

        LOGGER.debug('Deleting secret "%s"', self.configuration_url_secret_name)
        self.openshift.delete("secret", self.configuration_url_secret_name)

    def reload(self):
        self.openshift.rollout(self.deployment)


# pylint: disable=too-many-instance-attributes
class TLSApicast(TemplateApicast):
    """Gateway deployed with TLS certificates."""

    def __init__(self, staging: bool, configuration, openshift) -> None:
        super().__init__(staging, configuration, openshift)

        self.service_name = self.deployment
        self.secret_name = f"{self.deployment}-secret"
        self.volume_name = f"{self.deployment}-volume"
        self.mount_path = "/var/apicast/secrets"
        self.https_port = 8443

        self.cfssl_cert = CFSSLCertificate(
            host=configuration["cfssl"]["host"],
            port=configuration["cfssl"]["port"])
        self.cert_store = TmpCertificateStore()
        self.cert_manager = CertificateManager(self.cfssl_cert, self.cert_store)

    @property
    def endpoint(self):
        """Returns gateway endpoint."""
        return self.staging_endpoint if self.staging else self.production_endpoint

    @property
    def hostname(self):
        """Returns wildcard endpoint."""
        return urlparse(self.endpoint % "*").hostname

    def get_proxy_settings(self, service: Service, proxy_settings: Dict) -> Dict:
        entity_id = service.entity_id
        proxy_settings.update({
            "sandbox_endpoint": self.staging_endpoint % f"{entity_id}-staging",
            "endpoint": self.production_endpoint % f"{entity_id}-production",
        })
        return proxy_settings

    def register_service(self, service: Service):
        service_id = service.entity_id

        staging_name = f"{service_id}-staging"
        prod_name = f"{service_id}-production"

        staging_endpoint = urlparse(self.staging_endpoint % staging_name).hostname
        production_endpoint = urlparse(self.production_endpoint % prod_name).hostname

        LOGGER.debug('Creating routes for service "%s"', self.service_name)

        self.openshift.routes.create(staging_name, Routes.Types.PASSTHROUGH,
                                     service=self.service_name, hostname=staging_endpoint)
        self.openshift.routes.create(prod_name, Routes.Types.PASSTHROUGH,
                                     service=self.service_name, hostname=production_endpoint)

    def unregister_service(self, service: Service):
        service_id = service.entity_id

        LOGGER.debug('Deleting routes for service "%s"', self.service_name)

        del self.openshift.routes[f"{service_id}-staging"]
        del self.openshift.routes[f"{service_id}-production"]

    @property
    def _csr_names(self):
        """Returns data for Certificate Signing Request."""
        return {
            "O": self.hostname,
            "OU": "IT",
            "L": "San Francisco",
            "ST": "California",
            "C": "US",
        }

    def get_patch_data(self) -> Dict:
        """Returns patch data for enabling https port on service."""
        return {
            "spec": {
                "ports": [
                    {
                        "name": "https",
                        "port": self.https_port,
                        "protocol": "TCP"
                    }
                ],
            }
        }

    def _add_envs(self):
        LOGGER.debug('Adding envs to deployment "%s"...', self.deployment)

        envs = {
            "APICAST_HTTPS_PORT": self.https_port,
            "APICAST_HTTPS_CERTIFICATE": f"{self.mount_path}/tls.crt",
            "APICAST_HTTPS_CERTIFICATE_KEY": f"{self.mount_path}/tls.key",
        }
        LOGGER.debug(envs)
        self.openshift.environ(self.deployment).set_many(envs)

    def _create_secret(self):
        LOGGER.debug('Creating tls secret "%s"...', self.secret_name)

        cert = self.new_cert("server")

        pem = cert.certificate.encode("ascii")
        key = cert.key.encode("ascii")

        resource = {
            "kind": "Secret",
            "apiVersion": "v1",
            "metadata": {
                "name": self.secret_name,
            },
            "data": {
                "tls.crt": base64.b64encode(pem).decode("ascii"),
                "tls.key": base64.b64encode(key).decode("ascii"),
            }
        }

        self.openshift.apply(resource)

    def new_cert(self, label: str) -> CreateCertificateResponse:
        """Create a new ssl certificate.
        Args:
            :param label: A identifier for the certificate.
        Returns:
            certificate: Certificate PEM-like.
            private_key: Key PEM-like.
        """
        return self.cert_manager.create(label, self.hostname, hosts=[self.hostname],
                                        names=[self._csr_names])

    def get_cert(self, label: str) -> GetCertificateResponse:
        """Get existent certificate.
        Args:
            :param label: A identifier for the certificate.
        Returns:
            certificate: Certificate PEM-like.
            private_key: Key PEM-like.
        """
        return self.cert_store.get(label)

    def create(self):
        """Deploy TLS Apicast."""

        super().create()

        self._create_secret()

        LOGGER.debug('Adding volume "%s" bound to secret "%s" to deployment "%s"...',
                     self.volume_name, self.secret_name, self.deployment)
        self.openshift.add_volume(self.deployment, self.volume_name,
                                  self.mount_path, self.secret_name)

        self._add_envs()

        LOGGER.debug('Patching service "%s". Payload "%s"...', self.service_name, self.get_patch_data())
        self.openshift.patch("service", self.service_name, self.get_patch_data())

        LOGGER.debug('TLS apicast "%s" has been deployed!', self.deployment)

    def destroy(self):
        """Destroy TLS Apicast."""

        super().destroy()

        LOGGER.debug('Deleting secret "%s"', self.secret_name)
        self.openshift.delete("secret", self.secret_name)

        LOGGER.debug('TLS apicast "%s" has been destroyed!', self.deployment)
