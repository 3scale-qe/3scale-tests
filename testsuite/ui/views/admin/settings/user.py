"""View representations of User Account pages"""
from widgetastic.widget import TextInput
from widgetastic_patternfly4 import PatternflyTable

from testsuite.ui.navigation import step
from testsuite.ui.views.admin.settings import BaseSettingsView
from testsuite.ui.widgets import RadioGroup


# pylint: disable=invalid-overridden-method
class UsersView(BaseSettingsView):
    """View representation of Users Listing page"""
    path_pattern = '/p/admin/account/users'
    table = PatternflyTable('//*[@id="users"]')

    @step("UserDetailView")
    def detail(self, user_id):
        """Opens detail Account by ID"""
        self.table.row(_row__attr=('id', 'user_' + str(user_id))).name.click()

    def prerequisite(self):
        return BaseSettingsView

    @property
    def is_displayed(self):
        return self.table.is_displayed and self.path in self.browser.url


class UserDetailView(BaseSettingsView):
    """View representation of User Detail page"""
    path_pattern = '/p/admin/account/users/{user_id}/edit'
    username = TextInput(id='#user_username')
    email = TextInput(id='#user_email')
    password = TextInput(id='#user_password')
    organization = TextInput(id='#user_password_confirmation')
    role = RadioGroup('//*[@id="user_role_input"]')  # type:ignore
    permissions = RadioGroup('//*[@id="user_member_permissions_input"]',  # type:ignore
                             fieldset_id='FeatureAccessList')
    access_list = RadioGroup('//*[@id="user_member_permissions_input"]',  # type:ignore
                             fieldset_id='ServiceAccessList')

    def __init__(self, parent, user):
        super().__init__(parent, user_id=user.entity_id)

    def role_admin(self):
        """Set admin role for the User"""
        self.role.select('user_role_admin')

    def role_member(self):
        """Set member role for the User"""
        self.role.select('user_role_member')

    def add_permissions(self, *permissions):
        """
        Select chosen permissions for the User
        :param permissions: String id-s of permission check-boxes
        """
        self.permissions.select(permissions)

    def clear_permissions(self):
        """Remove all permissions for user"""
        self.permissions.clear_all()

    def clear_access_list(self):
        """Clear permissions for all services"""
        self.access_list.clear_all()

    def prerequisite(self):
        return UsersView

    @property
    def is_displayed(self):
        return self.username.is_displayed and self.email.is_displayed and self.role.is_displayed \
               and self.path in self.browser.url
