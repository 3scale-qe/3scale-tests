"""View representations of User Account pages"""
from widgetastic.widget import TextInput
from widgetastic_patternfly4 import PatternflyTable

from testsuite.ui.navigation import step
from testsuite.ui.views.admin.foundation import SettingsNavView
from testsuite.ui.widgets import RadioGroup


# pylint: disable=invalid-overridden-method
class UsersView(SettingsNavView):
    """View representation of Users Listing page"""
    endpoint_path = '/p/admin/account/users'
    table = PatternflyTable('//*[@id="users"]')

    @step("UserDetailView")
    def detail(self, user_id):
        """Opens detail Account by ID"""
        self.table.row(_row__attr=('id', 'user_' + str(user_id))).name.click()

    def prerequisite(self):
        return SettingsNavView

    def is_displayed(self):
        return self.table.is_displayed


class UserDetailView(SettingsNavView):
    """View representation of User Detail page"""
    endpoint_path = '/p/admin/account/users/{user_id}/edit'

    username = TextInput(id='#user_username')
    email = TextInput(id='#user_email')
    password = TextInput(id='#user_password')
    organization = TextInput(id='#user_password_confirmation')
    role = RadioGroup('//*[@id="user_role_input"]')  # type:ignore
    permissions = RadioGroup('//*[@id="user_member_permissions_input"]',  # type:ignore
                             fieldset_id='FeatureAccessList')
    access_list = RadioGroup('//*[@id="user_member_permissions_input"]',  # type:ignore
                             fieldset_id='ServiceAccessList')

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

    # pylint: disable=missing-function-docstring
    def clear_permissions(self):
        self.permissions.clear_all()

    def cleat_access_list(self):
        self.access_list.clear_all()

    def prerequisite(self):
        return UsersView

    def is_displayed(self):
        return self.username.is_displayed and self.email.is_displayed and self.role.is_displayed
