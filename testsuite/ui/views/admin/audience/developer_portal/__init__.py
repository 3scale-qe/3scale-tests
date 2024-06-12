"""View representations of Developer Portal section pages"""

from selenium.common.exceptions import NoSuchElementException
from wait_for import TimedOutError, wait_for
from widgetastic.widget import GenericLocatorWidget, TextInput, Text, FileInput, Image
from widgetastic_patternfly4 import PatternflyTable

from testsuite.ui.navigation import step
from testsuite.ui.views.admin.audience import BaseAudienceView
from testsuite.ui.widgets import (
    ThreescaleDropdown,
    DivBasedEditor,
    ThreescaleButtonGroup,
    ThreescaleCheckBox,
    CheckBoxGroup,
    APIDocsSelect,
)
from testsuite.ui.widgets.buttons import ThreescaleSubmitButton, ThreescaleDeleteButton, ThreescaleCreateButton


class CMSNewPageView(BaseAudienceView):
    """View representation of Developer Portal New Page page"""

    path_pattern = "/p/admin/cms/pages/new"
    title = TextInput(id="cms_template_title")
    section = ThreescaleDropdown(".//*[@id='cms_template_section_input']")
    path_input = TextInput(id="cms_template_path")
    layout_select = ThreescaleDropdown("//*[@id='cms_template_layout_id']")
    code = DivBasedEditor(locator="//*[contains(@class, 'CodeMirror cm-s-neat CodeMirror-wrap')]")
    advanced_options = GenericLocatorWidget(".//*[normalize-space(.)='Advanced options']")
    liquid_check_box = GenericLocatorWidget(locator=".//input[@id='cms_template_liquid_enabled']")
    submit = ThreescaleSubmitButton()

    # pylint: disable=too-many-arguments
    def create(self, title, section, path, page_html, layout=None, liquid_enabled=False):
        """Creates a new dev portal page"""
        self.title.fill(title)
        self.section.select_by_text(section)
        self.path_input.fill(path)
        self.code.fill(page_html)
        if layout:
            self.layout_select.select_by_text(layout)
        if liquid_enabled:
            self.advanced_options.click()
            self.liquid_check_box.click()
        self.submit.click()

    def prerequisite(self):
        return DeveloperPortalContentView

    @property
    def is_displayed(self):
        return (
            self.title.is_displayed
            and self.section.is_displayed
            and self.path_input.is_displayed
            and self.code.is_displayed
            and self.path in self.browser.url
        )


class CMSEditPageView(BaseAudienceView):
    """View representation of Developer Portal Edit Page page"""

    path_pattern = "/p/admin/cms/pages/{page_id}/edit"
    publish_button = GenericLocatorWidget(".//button[@title='Save and publish the current draft.']")
    path_input = TextInput(id="cms_template_path")
    delete_button = ThreescaleDeleteButton()
    code = DivBasedEditor(locator="//*[contains(@class, 'CodeMirror cm-s-neat CodeMirror-wrap')]")

    def __init__(self, parent, page_id):
        super().__init__(parent, page_id=page_id)

    def publish(self):
        """Publish dev portal page"""
        self.publish_button.click()

    def get_path(self):
        """Get path of dev portal page"""
        return self.path_input.value

    def delete(self):
        """Delete page of dev portal"""
        self.delete_button.click()

    def prerequisite(self):
        return DeveloperPortalContentView

    @property
    def is_displayed(self):
        return (
            self.publish_button.is_displayed
            and self.path_input.is_displayed
            and self.delete_button.is_displayed
            and self.path in self.browser.url
        )


class CMSNewSectionView(BaseAudienceView):
    """View representation of Developer Portal New Section page"""

    path_pattern = "/p/admin/cms/sections/new"
    title = TextInput(id="cms_section_title")
    public = ThreescaleCheckBox('//input[@id="cms_section_public"]')
    path_input = TextInput(id="cms_section_partial_path")
    submit = ThreescaleSubmitButton()

    def create(self, title, path, public=True):
        """Creates a new section of dev portal"""
        self.title.fill(title)
        self.public.check(public)
        self.path_input.fill(path)
        self.submit.click()

    def prerequisite(self):
        return DeveloperPortalContentView

    @property
    def is_displayed(self):
        return (
            self.title.is_displayed
            and self.public.is_displayed
            and self.path_input.is_displayed
            and self.submit.is_displayed
            and self.path in self.browser.url
        )


class CMSEditSectionView(BaseAudienceView):
    """View representation of Developer Portal Edit Section page"""

    path_pattern = "/p/admin/cms/builtin_sections/{section_id}/edit"
    title = TextInput(id="cms_section_title")
    public = ThreescaleCheckBox('//input[@id="cms_section_public"]')
    path_input = TextInput(id="cms_section_partial_path")
    delete_button = ThreescaleDeleteButton()

    def __init__(self, parent, section_id):
        super().__init__(parent, section_id=section_id)

    def delete(self):
        """Delete section of dev portal"""
        self.delete_button.click()

    def prerequisite(self):
        return DeveloperPortalContentView

    @property
    def is_displayed(self):
        return (
            self.title.is_displayed
            and self.public.is_displayed
            and self.path_input.is_displayed
            and self.delete_button.is_displayed
            and self.path in self.browser.url
        )


class DeveloperPortalContentView(BaseAudienceView):
    """View representation of Developer Portal Content page"""

    # path can be different when clicking from dashboard is '/p/admin/cms' and from menu is '/p/admin/cms/templates'
    path_pattern = "/p/admin/cms/templates"
    quick_links = Text("//a[@href='#quick-links']")
    snippets = Text("//a[@href='#tips-and-tricks']")
    button_group = ThreescaleButtonGroup(locator=".//*[@id='cms-new-content-button']")

    @step("CMSNewPageView")
    def new_page(self):
        """Create a new dev portal page"""
        self.button_group.select("/p/admin/cms/pages/new")

    @step("CMSEditPageView")
    def edit_page(self, page_id):
        """Edit a new dev portal page"""
        self.browser.element(f".//*[@href='/p/admin/cms/pages/{page_id}/edit']").click()

    @step("CMSNewSectionView")
    def new_section(self):
        """Create a new dev portal section"""
        self.button_group.select("/p/admin/cms/sections/new")

    @step("CMSEditSectionView")
    def edit_section(self, section_id):
        """Edit a new dev portal section"""
        self.browser.element(f".//*[@href='/p/admin/cms/sections/{section_id}/edit']").click()

    def prerequisite(self):
        return BaseAudienceView

    @property
    def is_displayed(self):
        return (
            self.quick_links.is_displayed
            and self.snippets.is_displayed
            and (self.path in self.browser.url or "/p/admin/cms" in self.browser.url)
        )


class DeveloperPortalLogoView(BaseAudienceView):
    """View representation of Developer Portal Logo edit page"""

    path_pattern = "/p/admin/account/logo/edit"
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
        return (
            BaseAudienceView.is_displayed.fget(self)
            and self.file_input.is_displayed
            and self.upload_button.is_displayed
            and self.path in self.browser.url
        )


class ActiveDocsView(BaseAudienceView):
    """View representation of Active Docs list page"""

    path_pattern = "/admin/api_docs/services"
    create_new_spec_link = Text("//a[@href='/admin/api_docs/services/new']")

    @step("ActiveDocsNewView")
    def create_new_spec(self):
        """Create new active docs specification"""
        self.create_new_spec_link.click()

    def prerequisite(self):
        return BaseAudienceView

    @property
    def is_displayed(self):
        return self.create_new_spec_link.is_displayed and self.path in self.browser.url


class ActiveDocsNewView(BaseAudienceView):
    """View representation of New Active Docs page"""

    path_pattern = "/admin/api_docs/services/new"
    create_spec_btn = ThreescaleCreateButton()
    skip_swagger_validation_checkbox = GenericLocatorWidget("#api_docs_service_skip_swagger_validations")
    name_field = TextInput(id="api_docs_service_name")
    sys_name_field = TextInput(id="api_docs_service_system_name")
    publish_checkbox = GenericLocatorWidget("//input[@id='api_docs_service_published_input']")
    description_field = TextInput(id="api_docs_service_description")
    service_selector = APIDocsSelect()
    json_spec = DivBasedEditor(locator="//*[contains(@class, 'CodeMirror cm-s-neat CodeMirror-wrap')]")

    # pylint: disable=too-many-arguments
    def create_spec(
        self, name, sys_name, description, service, oas_spec, publish_option=False, skip_validation_option=False
    ):
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
        self.service_selector.item_select(service.entity["name"])
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
        return (
            BaseAudienceView.is_displayed.fget(self)
            and self.create_spec_btn.is_displayed
            and self.sys_name_field.is_displayed
            and self.path in self.browser.url
        )


class BotProtection(BaseAudienceView):
    """View representation of Developer Portal's Spam Protection setup"""

    path_pattern = "/site/spam_protection/edit"
    no_protection = Text('//*[@id="settings_spam_protection_level_none"]')
    recaptcha_protection = Text('//*[@id="settings_spam_protection_level_captcha"]')
    submit_button = ThreescaleSubmitButton()

    def prerequisite(self):
        return BaseAudienceView

    def _submit_change(self):
        self.submit_button.click()

    def disable_protection(self):
        """
        Disables SPAM protection by selecting `No Protection` in UI and submits it.
        """
        self.no_protection.click()
        self._submit_change()

    def enable_protection(self):
        """
        Enables SPAM protection by selecting `Always` in UI and submits it.
        """
        self.recaptcha_protection.click()
        self._submit_change()

    @property
    def is_displayed(self):
        return (
            BaseAudienceView.is_displayed.fget(self)
            and self.path in self.browser.url
            and self.no_protection.is_displayed
            and self.recaptcha_protection.is_displayed
        )


class DeveloperPortalGroupView(BaseAudienceView):
    """View representation of Groups page"""

    path_pattern = "/p/admin/cms/groups"
    table = PatternflyTable(
        "//table[@aria-label='Groups table']",
        column_widgets={3: GenericLocatorWidget("./a[contains(@class, 'delete')]")},
    )
    create_button = GenericLocatorWidget(".//*[@href='/p/admin/cms/groups/new']")

    @step("DeveloperPortalGroupNewView")
    def create_new_group(self):
        """Create new group for developer portal"""
        self.create_button.click()

    def delete_group(self, group_name):
        """Delete group fro developer portal"""
        [x for x in self.table.rows() if x.name.text == group_name][0][2].click(handle_alert=True)

    def prerequisite(self):
        return BaseAudienceView

    @property
    def is_displayed(self):
        return BaseAudienceView.is_displayed.fget(self) and self.table.is_displayed and self.path in self.browser.url


class DeveloperPortalGroupNewView(BaseAudienceView):
    """View representation of Create Group page"""

    path_pattern = "/p/admin/cms/groups/new"
    name = TextInput(id="cms_group_name")
    allowed_section = CheckBoxGroup(locator="//*[@id='cms_group_section_ids_input']")
    submit = ThreescaleSubmitButton()

    def create(self, name, allowed_sections: list):
        """Creates a new dev portal group"""
        self.name.fill(name)
        self.allowed_section.check_by_text(allowed_sections)
        self.submit.click()

    def prerequisite(self):
        return DeveloperPortalGroupView

    @property
    def is_displayed(self):
        return (
            BaseAudienceView.is_displayed.fget(self)
            and self.name.is_displayed
            and self.allowed_section.is_displayed
            and self.path in self.browser.url
        )
