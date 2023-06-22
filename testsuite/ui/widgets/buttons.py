"""3scale specific buttons"""

# Following ignore is needed otherwise: Method 'fill' is abstract in class 'Widget' but is not overridden ...
# pylint: disable=abstract-method

import widgetastic_patternfly4


class Button(widgetastic_patternfly4.Button):
    """Some buttons in 3scale have 'pf-c-button' class missing"""

    def _generate_locator(self, *text, **kwargs):
        locator = super()._generate_locator(*text, **kwargs)
        return locator.replace("and contains(@class, 'pf-c-button')", "", 1)


class ThreescaleCreateButton(Button):
    """Specific Create button of 3scale pages"""

    def __init__(
        self,
        parent=None,
        locator=".//*[(self::a or self::button or (self::input and "
        "(@type='button' or @type='submit'))) and "
        "(contains(@class, 'create') or contains(text(), 'Create'))]",
        logger=None,
    ):
        super().__init__(parent=parent, locator=locator, logger=logger)


class ThreescaleDeleteButton(Button):
    """Specific Delete button of 3scale pages"""

    def __init__(
        self,
        parent=None,
        locator=".//*[(self::a or self::button or (self::input and "
        "(@type='button' or @type='submit'))) and "
        "(contains(@class, 'delete') or contains(text(), 'Delete'))]",
        logger=None,
    ):
        super().__init__(parent=parent, locator=locator, logger=logger)

    def click(self, handle_alert=True):
        """Perform click action with handling alert"""
        super().click(handle_alert)


class ThreescaleUpdateButton(Button):
    """Specific Update button of 3scale pages"""

    def __init__(
        self,
        parent=None,
        locator=".//*[(self::a or self::button or (self::input and "
        "(@type='button' or @type='submit'))) and "
        "(contains(@class, 'update') or contains(text(), 'Update'))]",
        logger=None,
    ):
        super().__init__(parent=parent, locator=locator, logger=logger)


class ThreescaleEditButton(Button):
    """Specific Edit button of 3scale pages"""

    def __init__(
        self,
        parent=None,
        locator=".//*[(self::a or self::button or (self::input and "
        "(@type='button' or @type='submit'))) and "
        "(contains(@class, 'edit') or contains(text(), 'Edit'))]",
        logger=None,
    ):
        super().__init__(parent=parent, locator=locator, logger=logger)


class ThreescaleSubmitButton(Button):
    """Specific Submit button of 3scale pages"""

    def __init__(self, parent=None, locator=".//*[(self::input or self::button) and @type='submit']", logger=None):
        super().__init__(parent, locator=locator, logger=logger)


class ThreescaleSearchButton(Button):
    """Specific Search button of 3scale pages"""

    def __init__(self, parent=None, locator="//button[contains(text(), 'Search')]", logger=None):
        super().__init__(parent=parent, locator=locator, logger=logger)
