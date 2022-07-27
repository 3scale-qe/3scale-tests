"""
Check if annotations of apicast-operator pod are present
"""
from typing import Tuple, List, Union

import pytest

from testsuite.capabilities import Capability

pytestmark = [
    pytest.mark.sandbag,  # requires apicast operator, doesn't have to be available
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-8314"),
    pytest.mark.required_capabilities(Capability.OCP4),
]

ANNOTATIONS_PRE_2_12: List[Union[Tuple[str, str], Tuple[str, None]]] = [
    ("support", "Red Hat"),
    ("repository", "https://github.com/3scale/apicast-operator"),
    ("operators.operatorframework.io/builder", None),
    ("capabilities", "Full Lifecycle"),
    ("categories", "Integration & Delivery"),
    ("certified", "false"),

]

ANNOTATIONS_POST_2_12: List[Union[Tuple[str, str], Tuple[str, None]]] = [
    ("support", "Red Hat"),
    ("repository", "https://github.com/3scale/apicast-operator"),
    ("operators.operatorframework.io/builder", "operator-sdk-v1.2.0"),
    ("capabilities", "Full Lifecycle"),
    ("categories", "Integration & Delivery"),
    ("certified", "false"),
    ("operators.openshift.io/valid-subscription", '["Red Hat Integration", "Red Hat 3scale API Management"]'),
]


@pytest.mark.before_apicast_operator_version("0.7.0")  # since threescale 2.12
@pytest.mark.parametrize("annotation,expected_value", ANNOTATIONS_PRE_2_12)
def test_labels_operator_old(annotation, expected_value, operator):
    """ Test labels of operator pod. """
    value = operator.get_annotation(annotation)
    assert value is not None
    if expected_value:
        assert value == expected_value


@pytest.mark.require_apicast_operator_version("0.7.0")
@pytest.mark.parametrize("annotation,expected_value", ANNOTATIONS_POST_2_12)
def test_labels_operator_new(annotation, expected_value, operator):
    """ Test labels of operator pod. """
    value = operator.get_annotation(annotation)
    assert value is not None
    if expected_value:
        assert value == expected_value
