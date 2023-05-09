"""
Check if annotations of operator pod are present
"""
from typing import Tuple, List, Union

import pytest
from packaging.version import Version  # noqa # pylint: disable=unused-import

from testsuite import TESTED_VERSION  # noqa # pylint: disable=unused-import
from testsuite.capabilities import Capability

pytestmark = [
    pytest.mark.sandbag,  # requires operator in same namespace
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-8314"),
    pytest.mark.required_capabilities(Capability.OCP4),
]

ANNOTATIONS_PRE_2_12: List[Union[Tuple[str, str], Tuple[str, None]]] = [
    ("support", "Red Hat"),
    ("repository", "https://github.com/3scale/3scale-operator"),
    ("operators.operatorframework.io/builder", None),
    ("capabilities", "Deep Insights"),
    ("categories", "Integration & Delivery"),
    ("certified", "false"),
]

ANNOTATIONS_POST_2_12: List[Union[Tuple[str, str], Tuple[str, None]]] = [
    ("support", "Red Hat"),
    ("repository", "https://github.com/3scale/3scale-operator"),
    ("operators.operatorframework.io/builder", "operator-sdk-v1.2.0"),
    ("capabilities", "Deep Insights"),
    ("categories", "Integration & Delivery"),
    ("certified", "false"),
    ("operators.openshift.io/valid-subscription", '["Red Hat Integration", "Red Hat 3scale API Management"]'),
]


@pytest.mark.skipif("TESTED_VERSION >= Version('2.12')")
@pytest.mark.parametrize("annotation,expected_value", ANNOTATIONS_PRE_2_12)
def test_labels_operator_old(annotation, expected_value, operator):
    """Test labels of operator pod."""
    value = operator.get_annotation(annotation)
    assert value is not None
    if expected_value:
        assert value == expected_value


@pytest.mark.skipif("TESTED_VERSION < Version('2.12')")
@pytest.mark.parametrize("annotation,expected_value", ANNOTATIONS_POST_2_12)
def test_labels_operator_new(annotation, expected_value, operator):
    """Test labels of operator pod."""
    value = operator.get_annotation(annotation)
    assert value is not None
    if expected_value:
        assert value == expected_value
