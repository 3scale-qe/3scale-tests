"""View representations of Developer Portal section pages"""
from widgetastic.widget import GenericLocatorWidget, TextInput, Text

from testsuite.ui.navigation import step
from testsuite.ui.views.admin.audience import BaseAudienceView
from testsuite.ui.widgets import ThreescaleDropdown, DivBasedEditor
from testsuite.ui.widgets.buttons import ThreescaleCreateButton


class DeveloperPortalContentView(BaseAudienceView):
    """View representation of Developer Portal Content page"""
    # path can be different when clicking from dashboard is '/p/admin/cms' and from menu is '/p/admin/cms/templates'
    path_pattern = '/p/admin/cms'
    open_portal_to_world_btn = Text("//a[@href='/site/dns/open_portal']")

    def prerequisite(self):
        return BaseAudienceView

    @property
    def is_displayed(self):
        return BaseAudienceView.is_displayed.fget(self) and self.open_portal_to_world_btn.is_displayed and \
               self.path in self.browser.url


class ActiveDocsView(BaseAudienceView):
    """View representation of Active Docs list page"""
    path_pattern = '/admin/api_docs/services'
    create_new_spec_link = Text("//a[@href='/admin/api_docs/services/new']")

    @step("ActiveDocsNewView")
    def create_new_spec(self):
        """Create new active docs specification"""
        self.create_new_spec_link.click()

    def prerequisite(self):
        return BaseAudienceView

    @property
    def is_displayed(self):
        return BaseAudienceView.is_displayed.fget(self) and self.create_new_spec_link.is_displayed and \
               self.path in self.browser.url


class ActiveDocsNewView(BaseAudienceView):
    """View representation of New Active Docs page"""
    path_pattern = '/admin/api_docs/services/new'
    create_spec_btn = ThreescaleCreateButton()
    skip_swagger_validation_checkbox = GenericLocatorWidget("#api_docs_service_skip_swagger_validations")
    name_field = TextInput(id="api_docs_service_name")
    sys_name_field = TextInput(id="api_docs_service_system_name")
    publish_checkbox = GenericLocatorWidget("#api_docs_service_published")
    description_field = TextInput(id="api_docs_service_description")
    service_selector = ThreescaleDropdown("//*[@id='api_docs_service_service_id']")
    json_spec = DivBasedEditor(locator="//*[contains(@class, 'CodeMirror cm-s-neat CodeMirror-wrap')]")

    # pylint: disable=too-many-arguments
    def create_spec(self, name, sys_name, description, service,
                    oas_spec, publish_option=False, skip_validation_option=False):
        """
        Create new active doc specification via UI
        :param name: Name of Active doc
        :param sys_name: System name of Active doc
        :param description: Description of Active doc
        :param service: Service of active doc
        :param oas_spec: oas specification in json format
        :param publish_option: True if should be published by default
        :param skip_validation_option: True if should skipp swagger validation
        """
        self.name_field.fill(name)
        self.sys_name_field.fill(sys_name)
        self.description_field.fill(description)
        self.service_selector.select_by_value(service.entity_id)
        self.json_spec.fill(oas_spec)

        if publish_option:
            self.publish_checkbox.click()
        if skip_validation_option:
            self.skip_swagger_validation_checkbox.click()

        self.create_spec_btn.click()

    def prerequisite(self):
        return ActiveDocsView

    @property
    def is_displayed(self):
        return BaseAudienceView.is_displayed.fget(self) and self.create_spec_btn.is_displayed and \
               self.sys_name_field.is_displayed and self.path in self.browser.url
