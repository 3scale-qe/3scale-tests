"""
Navigator takes responsibility of navigation process during UI testing.
It uses two basic structures (prerequisites and steps) in order to construct logical path (or sequence of actions)
from root View to desired location. This simulates user actions during system navigation.

Navigation process consists of two parts:
    1. Backtrace - Views should extend NavigateStep class which defines simple method `prerequisite`.
        This method should return/specify at least one View class that specific View is accessible from.
        Backtrace process then create queue that consists of View sequence that describes path from root
        to desired View.
    2. Perform of steps - Sequentially pops Views from mentioned queue and invoke methods that are decorated
        as steps for navigation.

Design of this navigation is based on: https://github.com/RedHatQE/navmazing
"""
import inspect
from collections import deque
from typing import TypeVar, Callable, TYPE_CHECKING, Any

from testsuite.ui.browser import ThreeScaleBrowser

if TYPE_CHECKING:
    # pylint: disable=cyclic-import
    from testsuite.ui.views.admin import BaseAdminView  # noqa

ReturnView = TypeVar("ReturnView", bound="BaseAdminView")


def step(cls, **kwargs):
    """
    Decorator for methods invoking new page or View.
    Within Navigator context, such method is referred as a step, that is performed
    in order to switch from one View to another (from one page to another).

    Parameter cls may contain two variants:
        1. Class or it's String value
        2. Key word that begins with "@". Currently supported:
            2.1 "@href" - method decorated with `@step("@href") expects String parameter
                that will be usually matched with <a href="">. This is just recommendation and
                user is responsible for correct implementation of such method.
    Args:
        :param cls: String name of View that is accessible with particular step
        :param kwargs: required by Views as part of query string
    """

    # pylint: disable=protected-access
    def decorator(function):
        function._class_name = cls
        function._kwargs = kwargs
        return function

    return decorator


class Navigator:
    """Responsible for Views navigation"""

    def __init__(self, browser, base_views):
        """
        Initializes Navigator with Browser instance and list of base Views.
        Base Views are specifically chosen to represent root elements in navigation tree (without any prerequisites)
        Args:
            :param browser: instance of browser
            :param base_views: Views that are roots in prerequisite hierarchy (does not have any prerequisite)
        """
        self.page_chain = deque()
        self.browser = browser
        self.base_views = base_views

    def navigate(self, cls: Callable[[ThreeScaleBrowser], ReturnView], **kwargs) -> ReturnView:
        """
        Perform navigation to specific View. If required by particular steps, args and kwargs
        should be specified. They are later passed to avery step method and mapped to
        correct View parameters.
        Args:
            :param cls: Class of desired View
            :return: Instance of the current View
        """
        self.page_chain.clear()
        self._backtrace(cls, **kwargs)
        return self._perform_steps(**kwargs)

    def new_page(self, cls, **kwargs):
        """Creates a new instance of class with necessary arguments."""
        signature = inspect.signature(cls.__init__)
        filtered_kwargs = {key: value for key, value in kwargs.items() if key in signature.parameters}
        return cls(self.browser, **filtered_kwargs)

    def open(self, cls: Callable[[ThreeScaleBrowser, Any], ReturnView], **kwargs) -> ReturnView:
        """
        Directly opens desired View, by inserting its `endpoint_path` in to browser
        Args:
            :param cls: Class of desired View
            :return: Instance of the opened View
        """
        page = self.new_page(cls, **kwargs)
        self.browser.set_path(page.endpoint_path)
        return page

    def _backtrace(self, cls, **kwargs):
        """
        Recursively constructs logical path from root to navigated element. This path is saved in queue `page_chain`
        Args:
            :param page_cls: currently processed View class
        """
        page = self.new_page(cls, **kwargs)
        self.page_chain.append(page)
        if cls in self.base_views or page.is_displayed:
            return
        self._backtrace(page.prerequisite(), **kwargs)

    # pylint: disable=protected-access
    def _perform_steps(self, **kwargs):
        """
        This method recursively iterates list of Views (`page_chain`):
            from root (current View) to desired destination.
        Each iteration represent one step - one UI action that changes one View to another.
        """
        if len(self.page_chain) == 1:
            return self.page_chain[0]
        page = self.page_chain.pop()
        dest = self.page_chain[-1]

        possible_steps = inspect.getmembers(page, lambda o: hasattr(o, '_class_name'))
        if self._invoke_step(possible_steps, dest, **kwargs):
            dest.post_navigate(**kwargs)
            return self._perform_steps(**kwargs)
        raise NavigationStepNotFound(page, dest, possible_steps)

    def _invoke_step(self, possible_steps, destination, **kwargs):
        """
        Perform one step. This method invokes method that is decorated with @step.
        See `step(cls, **kwargs)` correct usage.

        :param possible_steps: list of tuples [(method name, method)]. Describes all View methods
            decorated with @step
        :param destination: View class
        :param kwargs: parameters that are passed to particular steps. E.g. account_id={id}
        :return: Bool value representing if step was preformed or not
        """
        alternative_steps = []
        for _, method in possible_steps:
            key_word = method._class_name
            if key_word == destination.__class__.__name__:
                signature = inspect.signature(method)
                filtered_kwargs = {key: value for key, value in kwargs.items() if key in signature.parameters}
                bound = signature.bind(**filtered_kwargs)
                bound.apply_defaults()
                try:
                    method(*bound.args, **bound.kwargs)
                except Exception as exc:
                    raise NavigationStepException(method.__dict__, destination, method) from exc
                return True
            if key_word.startswith('@'):
                alternative_steps.append(method)

        return self._invoke_alternative_step(alternative_steps, destination)

    @staticmethod
    def _invoke_alternative_step(alternative_steps, destination):
        """
        Alternative steps begins with "@".
        See `step(cls, **kwargs)` for alternatives.

        :param alternative_steps: list of tuples [(method name, method)]. Describes all View methods
            decorated with @step
        :param destination: View class
        :return: Bool value representing if step was preformed or not
        """
        for method in alternative_steps:
            if method._class_name.startswith('@href'):
                try:
                    method(destination.endpoint_path)
                except Exception as exc:
                    raise NavigationStepException(method.__dict__, destination, method) from exc
                return True
        return False


class NavigationStepNotFound(Exception):
    """Exception when navigations can't be found"""

    def __init__(self, current, dest, possibilities):
        super().__init__(self)
        self.current = current
        self.dest = dest
        self.possibilities = possibilities

    def __str__(self):
        return (
            "Couldn't find step to destination View: [{}] from current View: [{}]."
            " Following steps were available: [{}]"
        ).format(self.dest, self.current, ", ".join(list(self.possibilities)))


class NavigationStepException(Exception):
    """Exception when navigation fails on `@step` method"""

    def __init__(self, current, dest, step):
        super().__init__(self)
        self.current = current
        self.dest = dest
        self.step = step

    def __str__(self):
        return (
            "Step from current [{}] View to destination [{}] View failed"
            " during method invocation: [{}]"
        ).format(self.dest, self.current, self.step)


class Navigable:
    """Adds simple methods that helps with navigation"""

    # TODO: Navigation Exceptions

    def prerequisite(self):
        """
        Method that specifies prerequisite Views that must be visible in order to access required page.

        def prerequisite(self):
            return BaseAdminView

        This example will assure, that BaseAdminView must be present on the browser before further
        navigation steps can be taken.
        This is a default and is generally overridden.
        """

    def alternative_views(self):
        """
        Specify alternative Views that can be returned after navigation e.g. "Not Found 404"
        This is a default and is generally overridden.
        """

    def post_navigate(self, **kwargs):
        """
        Method is invoked when page is opened or navigated to. This method is called even when
        page is not destination page and is in the middle of page_chain.
        """
