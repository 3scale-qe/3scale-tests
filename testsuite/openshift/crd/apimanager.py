"""Module containing APIManager object"""
from typing import Optional, Set

from openshift_client import APIObject, Missing


def _locator(path, apiobj):
    """
    Translates string path like 'spec/backend/replicas' to an actual object
    """
    split = path.split("/")
    last_fragment = split[-1]
    current_fragment = apiobj.model
    for fragment in split[:-1]:
        if current_fragment[fragment] is Missing:
            return Missing, last_fragment
        current_fragment = current_fragment[fragment]
    return current_fragment, last_fragment


class APIManager(APIObject):
    """Wrapper on top of APIObject for specifically working with APIManager CRD"""

    ALL_DEPLOYMENTS = {
        "apicast-staging",
        "backend-cron",
        "backend-listener",
        "backend-redis",
        "backend-worker",
        "system-memcache",
        "system-mysql",
        "system-redis",
        "zync",
        "zync-database",
        "zync-que",
        "apicast-production",
        "system-app",
        "system-sidekiq",
        "system-sphinx",
    }

    def set_path(self, path, value, apiobj=None):
        """Sets value to a path in a string form"""
        apiobj = apiobj or self
        field, last_fragment = _locator(path, apiobj)
        if field is Missing:
            raise ValueError("Path does not exist")
        field[last_fragment] = value

    def get_path(self, path, apiobj=None):
        """Returns value from a path in a string form"""
        apiobj = apiobj or self
        field, last_fragment = _locator(path, apiobj)
        return field[last_fragment]

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

    def _scale(self, spec_locator, deployments, replicas, wait_for_replicas=None):
        """Generic scale function that requires path where to set replicas and on which deployments to wait"""
        current_replicas = self.get_path(spec_locator)
        # APIManager consider 1 replica as default and doesn't set the value in CRD by default
        if current_replicas is Missing:
            current_replicas = 1
        wait_for_replicas = wait_for_replicas or current_replicas

        # Safer way than using only apply()
        def _modify(apiobj):
            self.set_path(spec_locator, replicas, apiobj)

        # pylint: disable=unused-argument
        def _success(obj):
            if replicas > 0:
                return self._status_check(obj.model.status.deployments.ready, deployments=deployments)
            return self._status_check(obj.model.status.deployments.stopped, deployments=deployments)

        _, success = self.modify_and_apply(modifier_func=_modify)
        assert success
        self.self_selector().until_any(min_to_satisfy=wait_for_replicas, success_func=_success)
        return current_replicas

    def scale_backend(self, replicas, wait_for_replicas=None):
        """
        Scales the backend to specific replica count
        :returns number of replicas before the scaling
        """
        return self._scale(
            spec_locator="spec/backend/listenerSpec/replicas",
            deployments={"backend-listener"},
            replicas=replicas,
            wait_for_replicas=wait_for_replicas,
        )

    def scale_apicast_production(self, replicas, wait_for_replicas=None):
        """
        Scales the production apicast to specific replica count
        :returns number of replicas before the scaling
        """
        return self._scale(
            spec_locator="spec/apicast/productionSpec/replicas",
            deployments={"apicast-production"},
            replicas=replicas,
            wait_for_replicas=wait_for_replicas,
        )
