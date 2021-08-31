"""3scale specific buttons"""

from widgetastic_patternfly4 import Button


# pylint: disable=abstract-method
class ThreescaleCreateButton(Button):
    """Specific Create button of 3scale pages"""

    def __init__(self, parent=None, locator="//*[contains(text(), 'Create')]", logger=None):
        super().__init__(parent=parent, locator=locator, logger=logger)


class ThreescaleDeleteButton(Button):
    """Specific Delete button of 3scale pages"""

    def __init__(self, parent=None, locator="//*[contains(@class, 'delete')]", logger=None):
        super().__init__(parent=parent, locator=locator, logger=logger)

    def click(self, handle_alert=True):
        """Perform click action with handling alert"""
        super().click(handle_alert)


class ThreescaleUpdateButton(Button):
    """Specific Update button of 3scale pages"""

    def __init__(self, parent=None, locator="//*[contains(text(), 'Update')]", logger=None):
        super().__init__(parent=parent, locator=locator, logger=logger)


class ThreescaleEditButton(Button):
    """Specific Edit button of 3scale pages"""

    def __init__(self, parent=None, locator="//*[contains(@class, 'edit')]", logger=None):
        super().__init__(parent=parent, locator=locator, logger=logger)


class ThreescaleSubmitButton(Button):
    """Specific Submit button of 3scale pages"""

    def __init__(self, parent=None, locator="//*[(self::input or self::button) and @type='submit']", logger=None):
        super().__init__(parent, locator=locator, logger=logger)


class ThreescaleSearchButton(Button):
    """Specific Create button of 3scale pages"""

    def __init__(self, parent=None, locator="//button[contains(text(), 'Search')]", logger=None):
        super().__init__(parent=parent, locator=locator, logger=logger)
