"""APIcast CRD object"""
from openshift import APIObject, Context

from testsuite.openshift.client import OpenShiftClient


class APIcast(APIObject):
    """APIcast CRD object supporting modifying all attributes"""

    @classmethod
    def create_instance(cls, openshift: OpenShiftClient, name, labels=None):
        """
        Creates new barebone instance, that can be customized with additional attributes before committing.
        :param openshift:       Openshift object instance
        :param name:            Name of the resource
        :param labels:          Labels
        :return: Uncommited APIcast instance
        """

        model = {
            "apiVersion": "apps.3scale.net/v1alpha1",
            "kind": "APIcast",
            "metadata": {"name": name, "namespace": openshift.project_name},
            "spec": {"adminPortalCredentialsRef": {"name": name}},
        }
        if labels is not None:
            # Mypy incorrectly infers type of model as Collection[str]
            model["metadata"]["labels"] = labels  # type: ignore

        # Ensure that the object is created with the correct execution context
        context = Context()
        context.project_name = openshift.project_name
        context.api_url = openshift.server_url
        context.token = openshift.token

        return cls(model, context=context)

    def commit(self):
        """
        Creates object on the server and returns created entity.
        It will be the same class but attributes might differ, due to server adding/rejecting some of them.
        """
        self.create(["--save-config=true"])
        return self.refresh()

    # pylint: disable=arguments-differ
    # I am only adding optional argument, so it shouldn't be a big problem
    def modify_and_apply(self, modifier_func, retries=2, cmd_args=None, ignore_errors=False):
        """Modified version which asserts that it succeeds"""
        result, success = super().modify_and_apply(modifier_func, retries, cmd_args)
        if not ignore_errors:
            assert success, result.err()
        return result, success

    # Direct access to spec attributes, since all of the attributes are located directly there
    def __getitem__(self, item):
        return self.model.spec.get(item, default=None)

    def __setitem__(self, key, value):
        self.model.spec[key] = value

    def __delitem__(self, key):
        del self.model.spec[key]
