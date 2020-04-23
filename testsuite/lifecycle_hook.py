"""An interface for the testsuite to alter life-cycle of 3scale objects"""

# pylint: disable=no-self-use

import abc

from threescale_api.resources import Application, Service, Backend


class LifecycleHook(abc.ABC):
    """An interface to alter creation of 3scale objects

    This defines certain methods that are called during initialization of test
    environment at certain phases. It is supposed to provide mechanism to
    perform custom action certain 3scale objects (service and application)
    during their creation and/or deletion.

    This class exists mainly for documentation purposes. Anyway it can be
    sub-classed with desired methods/hooks overwritten"""

    def before_service(self, service_params: dict) -> dict:
        """Called before service is created

        This is allowed to modify passed service_params and proxy_params and
        they have to be returned as tuple. Returned values are used to create
        and update the service.

        Args:
            :param service_params: Params dict passed to 3scale api when creating the service
            :param proxy_params: Params dict used to setup/update proxy after service creation

        Returns:
            :returns: service_params"""

        return service_params

    # pylint: disable=unused-argument
    def before_proxy(self, service: Service, proxy_params: dict):
        """Called after the service is created to update its proxy configuration

        Allows to modify proxy parameters that will be used in said service proxy after it has been created.
        Args:
            :param service: Service whose proxy is being updated
            :param proxy_params: Params dict used to setup/update proxy after service creation

        Returns:
            :returns: proxy_params"""
        return proxy_params

    def on_service_create(self, service: Service):
        """Called right after service creation.

        Args:
            :param service: Newly created service"""

    def on_service_delete(self, service: Service):
        """Called right before service deletion

        Args:
            :param service: The service to be deleted"""

    def before_backend(self, backend_params: dict) -> dict:
        """Called before backend is created

        This is allowed to modify passed backend_params Returned value used to create
        backend.

        Args:
            :param backend_params: Params dict passed to 3scale api when creating the service
            :param proxy_params: Params dict used to setup/update proxy after service creation

        Returns:
            :returns: Backend params dict"""

        return backend_params

    def on_backend_create(self, backend: Backend):
        """Called right after Backend creation.

        Args:
            :param backend: Newly created backend"""

    def on_backend_delete(self, backend: Backend):
        """Called right before backend deletion

        Args:
            :param backend: The backend to be deleted"""

    def before_application(self, application_params: dict) -> dict:
        """Called before application is created

        This can modify application_params before they are passed to 3scale
        call for application creation. It has to return modified params.
        Returned value is then used to create application.

        Args:
            :param application_params: Params dict supposed to be passed to 3scale api when creating the application

        Returns:
            :returns: Application params dict"""

        return application_params

    def on_application_create(self, application: Application):
        """Called right after application is created.

        Args:
            :param application: Newly created application"""

    def on_application_delete(self, application: Application):
        """Called before application is deleted.

        Args:
            :param application: The application to be deleted"""
