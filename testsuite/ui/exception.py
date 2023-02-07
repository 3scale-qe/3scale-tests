"""UI exception classes"""


class UIException(Exception):
    """Generic exception for all UI errors"""


class ReadOnlyWidgetError(UIException):
    """Exception raised when trying to fill a read only widget"""


class DisabledWidgetError(UIException):
    """Exception raised when a widget is disabled"""


class DestinationNotDisplayedError(UIException):
    """Raised when navigation destination view was not displayed"""


class WebDriverError(UIException):
    """Raised when webdriver problem occurs"""


class ItemNotPresentException(Exception):
    """Raised when item in element is not present"""
