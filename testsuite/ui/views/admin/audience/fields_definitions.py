"""View representations of Fields Definitons pages"""
from widgetastic.widget import TextInput
from widgetastic_patternfly4 import Button

from testsuite.ui.navigation import step
from testsuite.ui.views.admin.audience import BaseAudienceView
from testsuite.ui.widgets.buttons import ThreescaleCreateButton


class FieldsDefinitionsView(BaseAudienceView):
    """View representation of Fields Definitons page"""

    path_pattern = "/admin/fields_definitions"
    user_create_button = Button(locator="//*[contains(@href, 'User')]")

    @step("FieldsDefinitionsCreateView")
    def new_definition(self):
        """
        Creates new Field Definition
        """
        self.user_create_button.click()

    def prerequisite(self):
        return BaseAudienceView

    @property
    def is_displayed(self):
        return (
            BaseAudienceView.is_displayed.fget(self)
            and self.user_create_button.is_displayed
            and self.path in self.browser.url
        )


class FieldsDefinitionsCreateView(BaseAudienceView):
    """View representation of Fields Definitons page"""

    path_pattern = "/admin/fields_definitions"
    name = TextInput(id="fields_definition_name")
    label = TextInput(id="fields_definition_label")
    create_button = ThreescaleCreateButton()

    def create_definition(self, name, label):
        """Create custom field definition"""
        self.name.fill(name)
        self.label.fill(label)
        self.create_button.click()

    def prerequisite(self):
        return FieldsDefinitionsView

    @property
    def is_displayed(self):
        return (
            BaseAudienceView.is_displayed.fget(self)
            and self.name.is_displayed
            and self.label.is_displayed
            and self.create_button.is_displayed
            and self.path in self.browser.url
        )
