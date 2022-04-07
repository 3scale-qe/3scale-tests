"""View representations of User Account pages"""
import enum
from typing import List

from widgetastic.widget import TextInput, Text
from widgetastic_patternfly4 import PatternflyTable

from testsuite.ui.navigation import step
from testsuite.ui.views.admin.settings import BaseSettingsView
from testsuite.ui.widgets import CheckBoxGroup, RadioGroup
from testsuite.ui.widgets.buttons import ThreescaleUpdateButton


class Scopes(enum.Enum):
    """Tokens scopes"""
    BILLING = 'user_member_permission_ids_finance'
    DEV_PORTAL = 'user_member_permission_ids_portal'
    SETTINGS = 'user_member_permission_ids_settings'
    ACCOUNT_APPLICATION = 'user_member_permission_ids_partners'
    ANALYTICS = 'user_member_permission_ids_monitoring'
    APP_PLANS = 'user_member_permission_ids_plans'
    POLICY = 'user_member_permission_ids_policy_registry'


# pylint: disable=invalid-overridden-method
class UsersView(BaseSettingsView):
    """View representation of Users Listing page"""
    path_pattern = '/p/admin/account/users'
    table = PatternflyTable('//*[@id="users"]', column_widgets={
        4: Text("./a[contains(@class, 'delete')]"),
        5: Text("./a[contains(@class, 'edit')]")
    })

    @step("UserDetailView")
    def detail(self, user):
        """Opens detail Account by ID"""
        self.table.row(_row__attr=('id', 'user_' + str(user.entity_id)))[5].widget.click()

    def delete(self, user):
        """Delete user by ID"""
        self.table.row(_row__attr=('id', 'user_' + str(user.entity_id)))[4].widget.click()

    def prerequisite(self):
        return BaseSettingsView

    @property
    def is_displayed(self):
        return BaseSettingsView.is_displayed.fget(self) and self.table.is_displayed and self.path in self.browser.url


class UserDetailView(BaseSettingsView):
    """View representation of User Detail page"""
    path_pattern = '/p/admin/account/users/{user_id}/edit'
    username = TextInput(id='#user_username')
    email = TextInput(id='#user_email')
    password = TextInput(id='#user_password')
    organization = TextInput(id='#user_password_confirmation')
    update_btn = ThreescaleUpdateButton()
    role = RadioGroup('//*[@id="user_role_input"]')

    permissions = CheckBoxGroup('//*[@id="user_member_permissions_input"]',  # type:ignore
                                ol_identifier='FeatureAccessList')
    access_list = CheckBoxGroup('//*[@id="user_member_permissions_input"]',  # type:ignore
                                ol_identifier='ServiceAccessList')

    def __init__(self, parent, user):
        super().__init__(parent, user_id=user.entity_id)

    def set_admin_role(self):
        """Set admin role for the User"""
        self.role.select('user_role_admin')

    def set_member_role(self):
        """Set member role for the User"""
        self.role.select('user_role_member')

    def check_all_products(self):
        """Allow permissions for all products"""
        self.permissions.check(['user_member_permission_ids_services'])

    def uncheck_all_products(self):
        """Allow permissions for all products"""
        self.permissions.uncheck(['user_member_permission_ids_services'])

    def add_permissions(self, scope: List[Scopes]):
        """
        Select chosen permissions for the User
        :param scope: List of permissions scopes from class Scopes
        """
        self.permissions.check(scope)

    def remove_permissions(self, scope: List[Scopes]):
        """
        Unselect chosen permissions for the User
        :param scope: List of permissions scopes from class Scopes
        """
        self.permissions.uncheck(scope)

    def clear_permissions(self):
        """Remove all permissions for user"""
        self.permissions.clear_all()

    def clear_access_list(self):
        """Clear permissions for all services"""
        self.access_list.clear_all()

    def add_products_access(self, product_ids: List[int]):
        """Add access to products by its ids
        :param: product_ids: ID of services to add access to.
        """
        for prod_id in product_ids:
            self.access_list.check([f"user_member_permission_service_ids_{prod_id}"])

    def remove_products_access(self, product_ids: List[int]):
        """remove access to products by its ids
        :param: product_ids: ID of services to remove access to.
        """
        for prod_id in product_ids:
            self.access_list.uncheck([f"user_member_permission_service_ids_{prod_id}"])

    def prerequisite(self):
        return UsersView

    @property
    def is_displayed(self):
        return BaseSettingsView.is_displayed.fget(self) and self.username.is_displayed and\
               self.email.is_displayed and self.role.is_displayed and self.path in self.browser.url
