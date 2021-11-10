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
import logging
from collections import deque
from typing import TypeVar, Type, Optional

from widgetastic.widget import View

from testsuite.ui.navigation.exception import NavigationStepNotFound
from testsuite.ui.navigation.nav_rules import view_class, view_class_string, href, STEP_DEST

CustomView = TypeVar("CustomView", bound=View)


def step(cls, prerequisite=False):
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
        :param prerequisite:
        :param kwargs: required by Views as part of query string
    """

    class _NavStep:
        def __init__(self, function):
            self.function = function
            setattr(function, STEP_DEST, cls)

        def __set_name__(self, owner, name):
            if prerequisite:
                def add_prerequisite():
                    return owner

                setattr(cls, 'prerequisite', add_prerequisite)

        def __get__(self, obj, owner):
            return self.function.__get__(obj, owner)

        def __call__(self, method, *args, **kwargs):
            return self.function(*args, **kwargs)

    return _NavStep


# pylint: disable=too-few-public-methods
class ViewStepsProcessor:
    """
    Offers methods that interact with step methods from given View.
    """

    def __init__(self, current_view):
        """
        Extracts list of step methods from `current_view`
        Args:
            :param current_view: currently processed View
        """
        self.current_view = current_view
        self.step_methods = [i[1] for i in inspect.getmembers(current_view, lambda o: hasattr(o, STEP_DEST))]

    def invoke(self, destination, **kwargs):
        """
        This method invokes method that is decorated with `@step`. The correct step method is chosen
        from the `step_methods` by filters in a form of navigation rules.
        Args:
            :param destination: View desired destination
            :param kwargs: parameters that are passed to particular steps. E.g. account_id={id}
        """
        rules = [view_class, view_class_string, href]
        logging.debug("Navigator: finding step from {self.current_view} to {destination}")
        for rule in rules:
            # The list of rules is ordered by priority. If the first rule returns any result,
            # the method is invoked and other rules are skipped
            if any(rule(step, destination, **kwargs) for step in self.step_methods):
                logging.debug("Navigator: completed step from {self.current_view} to {destination}")
                return

        raise NavigationStepNotFound(self.current_view, destination, self.step_methods)


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

    def navigate(self, cls: Type[CustomView], **kwargs) -> CustomView:
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

    # pylint: disable=inconsistent-return-statements
    def open(self, cls: Type[CustomView] = None, url: str = None, **kwargs) -> Optional[CustomView]:
        """
        Directly opens desired View, by inserting its `path` in to browser or url
        Args:
            :param cls: Class of desired View
            :param url: Custom host URL
            :return: Instance of the opened View
        """
        if url:
            self.browser.url = url
            return None
        page = self.new_page(cls, **kwargs)
        self.browser.set_path(page.path)
        page.post_navigate(**kwargs)
        return page

    def _backtrace(self, cls, **kwargs):
        """
        Recursively constructs logical path from root to navigated element. This path is saved in queue `page_chain`
        Args:
            :param page_cls: currently processed View class
        """
        page = self.new_page(cls, **kwargs)
        self.page_chain.append(page)
        if page.is_displayed:
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

        ViewStepsProcessor(page).invoke(dest, **kwargs)
        dest.post_navigate(**kwargs)
        return self._perform_steps(**kwargs)


class Navigable:
    """Adds simple methods that helps with navigation"""

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
