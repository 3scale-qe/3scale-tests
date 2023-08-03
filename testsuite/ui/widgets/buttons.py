"""3scale specific buttons"""

# Following ignore is needed otherwise: Method 'fill' is abstract in class 'Widget' but is not overridden ...
# pylint: disable=abstract-method

import widgetastic_patternfly4
from widgetastic.xpath import quote


class Button(widgetastic_patternfly4.Button):
    """Some buttons in 3scale have 'pf-c-button' class missing"""

    def _generate_locator(self, *text, **kwargs):
        locator = super()._generate_locator(*text, **kwargs)
        return locator.replace("and contains(@class, 'pf-c-button')", "", 1)


class ThreescaleButton(widgetastic_patternfly4.Button):
    """A button with custom xpath locator definition

    Some elements in 3scale can be identified by either class **OR** text
    label. Widgetastic support just identification by class and text label,
    therefore a class with custom locator is needed.
    """

    def __init__(self, parent, text, classes, elm_id=None, **kwargs):
        base = "(self::a or self::button or (self::input and (@type='button' or @type='submit')))"
        classes = " and ".join(f"contains(@class, {quote(i)})" for i in classes)
        elm_id = f"and [@id={quote(elm_id)}]"
        conditions = f"(({classes}) or {elm_id} or contains(text(), {quote(text)}))"
        super().__init__(parent, locator=f".//*[{base} and {conditions}]", **kwargs)


class ThreescaleCreateButton(ThreescaleButton):
    """Specific Create button of 3scale pages"""

    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, "Create", classes=["create"], **kwargs)


class ThreescaleDeleteButton(ThreescaleButton):
    """Specific Delete button of 3scale pages"""

    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, "Delete", classes=["delete"], **kwargs)

    def click(self, handle_alert=True):
        """Change handle_alert to True by default

        Deletion requires and confirmation that an object should be really
        deleted, alert is always displayed and needs to be covered
        """
        super().click(handle_alert)


class ThreescaleUpdateButton(ThreescaleButton):
    """Specific Update button of 3scale pages"""

    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, "Update", classes=["update"], **kwargs)


class ThreescaleEditButton(ThreescaleButton):
    """Specific Edit button of 3scale pages"""

    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, "Edit", classes=["edit"], **kwargs)


class ThreescaleSubmitButton(widgetastic_patternfly4.Button):
    """Specific Submit button of 3scale pages"""

    def __init__(self, parent=None, locator=".//*[(self::input or self::button) and @type='submit']", logger=None):
        super().__init__(parent, locator=locator, logger=logger)


class ThreescaleSearchButton(widgetastic_patternfly4.Button):
    """Specific Search button of 3scale pages"""

    def __init__(self, parent=None, locator="//button[contains(text(), 'Search')]", logger=None):
        super().__init__(parent=parent, locator=locator, logger=logger)
