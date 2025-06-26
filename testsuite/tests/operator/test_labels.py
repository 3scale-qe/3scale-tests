"""
Check if labels of operator pod are present
"""

from typing import Tuple, List, Union

import pytest
from packaging.version import Version

from testsuite import TESTED_VERSION
from testsuite.capabilities import Capability

pytestmark = [
    pytest.mark.sandbag,  # requires operator in same namespace
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-7750"),
    pytest.mark.required_capabilities(Capability.OCP4),
    pytest.mark.nopersistence,
]

LABELS_PRE_2_12: List[Union[Tuple[str, str], Tuple[str, None]]] = [
    ("com.redhat.component-name", "3scale-operator"),
    ("com.redhat.component-type", "infrastructure"),
    ("com.redhat.component-version", None),
    ("com.redhat.product-name", "3scale"),
    ("com.redhat.product-version", None),
    ("control-plane", "controller-manager"),
]

LABELS_POST_2_12: List[Union[Tuple[str, str], Tuple[str, None]]] = [
    ("com.company", "Red_Hat"),
    ("control-plane", "controller-manager"),
    ("rht.comp", "3scale"),
    ("rht.comp_ver", None),
    ("rht.prod_name", "Red_Hat_Integration"),
    ("rht.prod_ver", None),
    ("rht.subcomp", "3scale_operator"),
    ("rht.subcomp_t", "infrastructure"),
]


@pytest.mark.skipif(TESTED_VERSION >= Version("2.12"), reason="TESTED_VERSION >= Version('2.12')")
@pytest.mark.parametrize("label,expected_value", LABELS_PRE_2_12)
def test_labels_operator_old(label, expected_value, operator):
    """Test labels of operator pod."""
    value = operator.get_label(label)
    assert value is not None
    if expected_value:
        assert value == expected_value


@pytest.mark.skipif(TESTED_VERSION < Version("2.12"), reason="TESTED_VERSION < Version('2.12')")
@pytest.mark.parametrize("label,expected_value", LABELS_POST_2_12)
def test_labels_operator_new(label, expected_value, operator):
    """Test labels of operator pod."""
    value = operator.get_label(label)
    assert value is not None
    if expected_value:
        assert value == expected_value
