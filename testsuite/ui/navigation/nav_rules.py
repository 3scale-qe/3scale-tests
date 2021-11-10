"""
Set of methods that define rules which are used by Navigator.ViewStepsProcessor to invoke correct step method.
Each method should take three arguments:
    1. step: currently processed step method
    2  dest: some indicator of View that is used as condition in the rule
    3. kwargs: that are passed to the step method when invoked

Step method is invoked when it satisfies particular rule.
"""
import inspect
import logging

from testsuite.ui.navigation.exception import NavigationStepException

STEP_DEST = "_step_destination"


def view_class(step, dest, **kwargs):
    """
    Returns True and invokes step method if method parameter: `STEP_DEST` contains class
    and is equal to requested View class.
    """
    step_dest = getattr(step, STEP_DEST)
    if inspect.isclass(step_dest) and step_dest == dest.__class__:
        _invoke_step_method(step, **kwargs)
        return True
    return False


def view_class_string(step, dest, **kwargs):
    """"
    Returns True and invokes step method  if method parameter: `STEP_DEST` contains string
    and is equal to requested View class name.
    """
    step_dest = getattr(step, STEP_DEST)
    if isinstance(step_dest, str) and step_dest == dest.__class__.__name__:
        _invoke_step_method(step, **kwargs)
        return True
    return False


# pylint: disable=unused-argument
def href(step, dest, **kwargs):
    """
    Returns True and invokes step method if `STEP_DEST` contains key word: `@href`.
    Step method is invoked with `path` View parameter as argument.
    """
    if getattr(step, STEP_DEST).startswith('@href'):
        logging.debug("Navigator: invoking step method marked with `@href` {step}")
        step(dest.path)
        return True
    return False


def _invoke_step_method(step, **kwargs):
    """
    Inspects step method signature, binds `kwargs` to its arguments and invokes it.
    """
    try:
        logging.debug("Navigator: invoking method {step}")
        signature = inspect.signature(step)
        filtered_kwargs = {key: value for key, value in kwargs.items() if key in signature.parameters}
        bound = signature.bind(**filtered_kwargs)
        bound.apply_defaults()
        step(*bound.args, **bound.kwargs)
    except Exception as exc:
        raise NavigationStepException(step) from exc
