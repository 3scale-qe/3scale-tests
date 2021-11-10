"""Navigator Exceptions"""


class NavigationStepNotFound(Exception):
    """Exception when navigations can't be found"""

    def __init__(self, current, dest, possibilities):
        super().__init__(self)
        self.current = current
        self.dest = dest
        self.possibilities = possibilities

    def __str__(self):
        return (
            f"Couldn't find step to destination View: [{self.dest}] from current View: [{self.current}]."
            f" Following steps were available: [{', '.join(list(self.possibilities))}]"
        )


class NavigationStepException(Exception):
    """Exception when navigation fails on `@step` method"""

    def __init__(self, step):
        super().__init__(self)
        self.step = step

    def __str__(self):
        return (
            f"FAILED: Step method invocation: [{self.step}]"
        )
