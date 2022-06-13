"""
Check if labels of apicast operator pod are present
"""
from typing import Tuple, List, Union

import pytest
from packaging.version import Version  # noqa # pylint: disable=unused-import

from testsuite import APICAST_OPERATOR_VERSION  # noqa # pylint: disable=unused-import
from testsuite.capabilities import Capability

pytestmark = [
    pytest.mark.sandbag,  # requires apicast operator, doesn't have to be available
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-7751"),
    pytest.mark.required_capabilities(Capability.OCP4)
]

LABELS_PRE_2_12: List[Union[Tuple[str, str], Tuple[str, None]]] = [
    ("app", "apicast"),
    ("control-plane", "controller-manager"),
]

LABELS_POST_2_12: List[Union[Tuple[str, str], Tuple[str, None]]] = [
    ("app", "apicast"),
    ("com.company", "Red_Hat"),
    ("control-plane", "controller-manager"),
    ("rht.comp", "3scale_apicast"),
    ("rht.comp_ver", None),
    ("rht.prod_name", "Red_Hat_Integration"),
    ("rht.prod_ver", None),
    ("rht.subcomp", "apicast_operator"),
    ("rht.subcomp_t", "infrastructure"),
]


@pytest.mark.skipif("APICAST_OPERATOR_VERSION >  Version('0.6.0')")  # since threescale 2.12
@pytest.mark.parametrize("label,expected_value", LABELS_PRE_2_12)
def test_labels_operator_old(label, expected_value, operator):
    """ Test labels of apicast operator pod. """
    value = operator.get_label(label)
    assert value is not None
    if expected_value:
        assert value == expected_value


@pytest.mark.skipif("APICAST_OPERATOR_VERSION <= Version('0.6.0')")
@pytest.mark.parametrize("label,expected_value", LABELS_POST_2_12)
def test_labels_operator_new(label, expected_value, operator, logger):
    """ Test labels of apicast operator pod. """
    logger.info("%(name)s labels from %(namespace)s: %(labels)s", operator.as_dict()["metadata"])
    value = operator.get_label(label)
    assert value is not None
    if expected_value:
        assert value == expected_value
