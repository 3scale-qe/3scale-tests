"""Module containing Operator object"""

import openshift_client as oc
from openshift_client import APIObject


class Operator(APIObject):
    """Operator CRD object with custom serializer and deserializer for pickle module"""

    def __getstate__(self):
        """
        Custom serializer for pickle module
        more info here: https://docs.python.org/3/library/pickle.html#object.__getstate__
        """
        return {
            "name": self.model.metadata.name,
            "context": self.context,
        }

    def __setstate__(self, state):
        """
        Custom deserializer for pickle module
        more info here: https://docs.python.org/3/library/pickle.html#object.__setstate__
        """
        with state["context"]:
            result = oc.selector(f"pod/{state['name']}").object_json()
            super().__init__(string_to_model=result)
