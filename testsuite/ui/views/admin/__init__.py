""""All views import to views.admin"""
# flake8: noqa
from .audience.account import AccountsDetailView, AccountsView, NewAccountView, AccountEditView, \
    AccountApplicationsView, UsageRulesView
from .audience.account_plan import AccountPlansView, NewAccountPlanView
from .settings.webhooks import WebhooksView
from .foundation import DashboardView, BaseAdminView, AccessDeniedView, NotFoundView
from .login import LoginView
from .wizard import WizardIntroView, WizardExplainView
from .settings.user import UsersView, UserDetailView
