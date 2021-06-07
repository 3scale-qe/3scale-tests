"""Apicast deployed with ApicastOperator"""
import time
from testsuite import utils

from testsuite.capabilities import Capability
from testsuite.openshift.client import OpenShiftClient
from testsuite.openshift.crd.apicast import APIcast
from testsuite.openshift.env import Environ

from .selfmanaged import SelfManagedApicast


class OperatorApicast(SelfManagedApicast):
    """Gateway for use with APIcast deployed by operator"""
    CAPABILITIES = {Capability.APICAST, Capability.PRODUCTION_GATEWAY}

    # pylint: disable=too-many-arguments
    def __init__(self, staging: bool, openshift: OpenShiftClient, name, portal_endpoint, randomize=False) -> None:
        # APIcast operator prepends apicast in front the deployment name
        super().__init__(staging, openshift, f"{name}-stage" if staging else name, randomize)
        self.portal_endpoint = portal_endpoint
        self.apicast = None

    @property
    def deployment(self):
        return f"apicast-{super().deployment}"

    @property
    def environ(self) -> Environ:
        raise NotImplementedError("Operator doesn't support environment")

    def reload(self):
        self.openshift.do_action("delete", ["pod", "--force",
                                            "--grace-period=0", "-l", f"deployment={self.deployment}"])
        # pylint: disable=protected-access
        self.openshift.wait_for_ready(self.deployment)

    def create(self):
        apicast = APIcast.create_instance(
            openshift=self.openshift,
            name=self.name,
            provider_url=self.portal_endpoint
        )
        apicast["logLevel"] = "info"
        apicast["openSSLPeerVerificationEnabled"] = False
        if self.staging:
            apicast["deploymentEnvironment"] = "staging"
            apicast["cacheConfigurationSeconds"] = 0
        else:
            apicast["deploymentEnvironment"] = "production"
            apicast["cacheConfigurationSeconds"] = 300

        self.apicast = apicast.commit()
        # Since apicast operator doesnt have any indication of status of the apicast, we need wait until deployment
        # is created
        time.sleep(2)
        # pylint: disable=protected-access
        self.openshift.wait_for_ready(self.deployment)

    def destroy(self):
        if self.apicast:
            self.apicast.delete(ignore_not_found=True)

    def get_logs(self, since_time=None):
        raise NotImplementedError()
