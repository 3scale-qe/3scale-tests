"provide fixtures for custom policy injection through operator"
import pytest
import backoff

from testsuite import rawobj
from testsuite.utils import blame, custom_policy


@pytest.fixture(scope="module")
def policy_settings():
    "return the example policy configuration"
    return rawobj.PolicyConfig("example", configuration={}, version="0.1")


@pytest.fixture(scope="module")
def secret_name(request):
    """return a unique name for the secret
    """
    return blame(request, "secret")


# pylint: disable=unused-argument
@pytest.fixture(scope="module")
def create_custom_policy_secret(openshift, secret_name):
    """Create an openshift secrets to use as custom policy based on https://github.com/3scale-qe/apicast-example-policy
    """
    secrets = openshift().secrets
    secrets.create(name=secret_name, string_data=custom_policy())
    yield
    del secrets[secret_name]


# pylint: disable=unused-argument
@pytest.fixture(scope="module")
def patch_apimanager(request, openshift, secret_name, create_custom_policy_secret):
    """Patch the apimanager CRD to add the custom policy added to apicast staging
    """
    apimanager = openshift().api_manager
    apimanager.modify_and_apply(lambda manager: manager.set_path(
        "spec/apicast/stagingSpec/customPolicies", [
                                {"name":
                                    "example",
                                    "version": "0.1",
                                    "secretRef":
                                    {"name": secret_name}
                                 }]))
    request.addfinalizer(lambda: apimanager.modify_and_apply(lambda manager: manager.set_path(
        "spec/apicast/stagingSpec/customPolicies", [])))

    @backoff.on_predicate(backoff.fibo, max_tries=10)
    def wait_for_starting(apimanager):
        """Check that apicast-staging is not in ready state
        """
        return not apimanager.ready({"apicast-staging"})

    @backoff.on_predicate(backoff.fibo, max_tries=12)
    def wait_for_ready(apimanager):
        """Waiting for both apicast being in readdy state
           to ensure that the whole apimanager is up and running.
           It needs a higher number of retries or it will  occasionally fail
        """
        return apimanager.ready({"apicast-staging", "apicast-production"})

    # We need to explicitly wait for the deployment being in starting state
    # before waiting for it to be ready, the operator needs time to reconcile
    # its state
    wait_for_starting(apimanager)
    wait_for_ready(apimanager)
