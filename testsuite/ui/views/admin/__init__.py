""""All views import to views.admin"""
# flake8: noqa
from .audience.account import AccountsDetailView, AccountsView, AccountNewView, AccountEditView, \
    AccountApplicationsView, UsageRulesView
from .audience.account_plan import AccountPlansView, NewAccountPlanView
from .settings.webhooks import WebhooksView
from .foundation import DashboardView, BaseAdminView, AccessDeniedView, NotFoundView
from .login import LoginView
from .settings.user import UsersView, UserDetailView
