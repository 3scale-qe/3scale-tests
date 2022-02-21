"""View representations of Developer Portal section pages"""
from selenium.common.exceptions import NoSuchElementException
from wait_for import TimedOutError, wait_for
from widgetastic.widget import GenericLocatorWidget, TextInput, Text, FileInput, Image

from testsuite.ui.navigation import step
from testsuite.ui.views.admin.audience import BaseAudienceView
from testsuite.ui.widgets import ThreescaleDropdown, DivBasedEditor
from testsuite.ui.widgets.buttons import ThreescaleSubmitButton, ThreescaleDeleteButton


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


class DeveloperPortalLogoView(BaseAudienceView):
    """View representation of Developer Portal Logo edit page"""
    path_pattern = '/p/admin/account/logo/edit'
    file_input = FileInput(id="profile_logo")
    upload_button = ThreescaleSubmitButton()
    delete_logo_button = ThreescaleDeleteButton()
    logo = Image('//*[@id="logo_container"]/img')

    def upload_logo(self, file):
        """Method choose logo and uploads it"""
        self.file_input.fill(file)
        self.upload_button.click()
        try:
            wait_for(lambda: self.logo.is_displayed and file.name in self.logo.src, timeout="10s", delay=0.2)
        except TimedOutError as exc:
            raise NoSuchElementException("The Logo is not displayed correctly") from exc

    def prerequisite(self):
        return BaseAudienceView

    @property
    def is_displayed(self):
        return BaseAudienceView.is_displayed.fget(self) and self.file_input.is_displayed and \
               self.upload_button.is_displayed and self.path in self.browser.url


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
    create_spec_btn = GenericLocatorWidget("//button[contains(text(), 'Create')]")
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
