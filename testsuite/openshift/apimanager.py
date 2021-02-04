"""Module containing APIManager object"""
from typing import Optional, Set

from openshift import APIObject, Missing


class APIManager(APIObject):
    """Wrapper on top of APIObject for specifically working with APIManager CRD"""
    ALL_DEPLOYMENTS = {'apicast-staging', 'backend-cron', 'backend-listener', 'backend-redis', 'backend-worker',
                       'system-memcache', 'system-mysql', 'system-redis', 'zync', 'zync-database', 'zync-que',
                       'apicast-production', 'system-app', 'system-sidekiq', 'system-sphinx'}

    def ready(self, deployments: Optional[Set[str]] = None):
        """
        Checks if said deployments are ready or not.
        If no deployments are supplied it will check for all deployments
        """
        return self._status_check(self.model.status.deployments.ready, deployments)

    def stopped(self, deployments: Optional[Set[str]] = None):
        """
        Checks if said deployments are stopped or not.
        If no deployments are supplied it will check for all deployments
        """
        return self._status_check(self.model.status.deployments.stopped, deployments)

    def _status_check(self, status, deployments: Optional[Set[str]] = None):
        deployments = deployments or self.ALL_DEPLOYMENTS

        if status is Missing:
            return False

        valid_deployments = set(status)
        return deployments.issubset(valid_deployments)

    def scale_backend(self, replicas, wait_for_replicas=None):
        """
        Scales the backend to specific replica count
        :returns number of replicas before the scaling
        """
        current_replicas = self.model.spec.backend.listenerSpec.replicas
        wait_for_replicas = wait_for_replicas or current_replicas

        # Safer way than using only apply()
        def _modify(apiobj):
            apiobj.model.spec.backend.listenerSpec.replicas = replicas

        # pylint: disable=unused-argument
        def _success(obj):
            if replicas > 0:
                return self._status_check(obj.model.status.deployments.ready, deployments={"backend-listener"})
            return self._status_check(obj.model.status.deployments.stopped, deployments={"backend-listener"})

        _, success = self.modify_and_apply(modifier_func=_modify)
        assert success
        self.self_selector().until_any(min_to_satisfy=wait_for_replicas, success_func=_success)
        return current_replicas
