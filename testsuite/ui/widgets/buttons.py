"""3scale specific buttons"""

from widgetastic.widget import GenericLocatorWidget
from widgetastic_patternfly4 import Button


# pylint: disable=abstract-method
class ThreescaleCreateButton(GenericLocatorWidget):
    """Specific Create button of 3scale pages"""

    def __init__(self, parent=None, locator="//*[contains(@class, 'create')]", logger=None):
        super().__init__(parent, locator, logger)


class ThreescaleDeleteButton(GenericLocatorWidget):
    """Specific Delete button of 3scale pages"""

    def __init__(self, parent=None, locator="//*[contains(@class, 'delete')]", logger=None):
        super().__init__(parent, locator, logger)

    def click(self, handle_alert=True):
        """Perform click action with handling alert"""
        super().click(handle_alert)


class ThreescaleUpdateButton(GenericLocatorWidget):
    """Specific Update button of 3scale pages"""

    def __init__(self, parent=None, locator="//*[contains(@class, 'update')]", logger=None):
        super().__init__(parent, locator, logger)


class ThreescaleEditButton(GenericLocatorWidget):
    """Specific Edit button of 3scale pages"""

    def __init__(self, parent=None, locator="//*[contains(@class, 'edit')]", logger=None):
        super().__init__(parent, locator, logger)


class ThreescaleSubmitButton(Button):
    """Specific Submit button of 3scale pages"""

    def __init__(self, parent=None, locator=".//button[@type='submit']", logger=None):
        super().__init__(parent, locator=locator, logger=logger)
