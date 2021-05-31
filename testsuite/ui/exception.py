"""UI exception classes"""


class ReadOnlyWidgetError(Exception):
    """Exception raised when trying to fill a read only widget"""


class DisabledWidgetError(Exception):
    """Exception raised when a widget is disabled"""


class DestinationNotDisplayedError(Exception):
    """Raised when navigation destination view was not displayed"""


class WebDriverError(Exception):
    """Raised when webdriver problem occurs"""


class ItemNotPresentException(Exception):
    """Raised when item in element is not present"""
