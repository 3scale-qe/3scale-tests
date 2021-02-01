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


def step(cls, **kwargs):
    """
    Decorator for methods invoking new page or View.
    Within Navigator context, such method is referred as a step, that is performed
    in order to switch from one View to another (from one page to another).
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


# pylint: disable=too-few-public-methods
class Navigator:
    """Responsible for Views navigation"""

    def __init__(self, browser, base_views):
        """
        Initializes Navigator with Browser instance and list of base Views.
        Base Views are specifically chosen to represent root elements in navigation tree (without any prerequisites)
        """
        self.page_chain = deque()
        self.browser = browser
        self.base_views = base_views

    def navigate(self, cls, **kwargs):
        """
        Perform navigation to specific View. If required by particular steps, args and kwargs
        should be specified. They are later passed to avery step method and mapped to
        correct View parameters.
        Args:
            :param cls: Class of desired View
            :return: Instance of the current View
        """
        self.page_chain.clear()
        self._backtrace(cls)
        self._perform_steps(**kwargs)

        return cls(self.browser)

    def open(self, cls, **kwargs):
        """Directly opens desired View, by inserting its `endpoint_path` in to browser"""
        page = cls(self.browser)
        self.browser.set_path(page.endpoint_path.format(**kwargs))
        return page

    def _backtrace(self, page_cls):
        """
        Recursively constructs logical path from root to navigated element. This path is saved in queue `page_chain`
        Args:
            :param page_cls: currently processed View class
        """
        page = page_cls(self.browser)
        self.page_chain.append(page)
        if page_cls in self.base_views or page.is_displayed():
            return
        self._backtrace(page.prerequisite())

    # pylint: disable=protected-access
    # pylint: disable=expression-not-assigned)
    def _perform_steps(self, **kwargs):
        """
        Pops View from queue, finds correct method (step) and invoke it
        """
        if len(self.page_chain) == 1:
            return
        page = self.page_chain.pop()
        dest = self.page_chain[-1]

        for _, method in inspect.getmembers(page, predicate=inspect.ismethod):
            if hasattr(method, '_class_name'):
                if method._class_name.startswith('@href'):
                    method(dest.endpoint_path)
                    self._perform_steps(**kwargs)
                if method._class_name == dest.__class__.__name__:
                    self._invoke_step(method, kwargs)
                    self._perform_steps(**kwargs)

    @staticmethod
    def _invoke_step(method, kwargs):
        """
        Assign arguments passed to navigation with step method parameters and performs step
        :param method: method that parameters are being inspected
        :param kwargs: arguments passed to navigation
        """
        signature = inspect.signature(method)
        filtered_kwargs = {key: value for key, value in kwargs.items() if key in signature.parameters}
        bound = signature.bind(**filtered_kwargs)
        bound.apply_defaults()
        method(*bound.args, **bound.kwargs)


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

    def alternative_views(self, *args, **kwargs):
        """
        Specify alternative Views that can be returned after navigation e.g. "Not Found 404"
        This is a default and is generally overridden.
        """
