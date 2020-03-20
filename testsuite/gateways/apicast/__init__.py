"""Collection of apicast gateways with different deployments or options"""
# flake8: noqa
from .system import SystemApicast, SystemApicastRequirements
from .containers import ContainerizedApicast
from .operator import OperatorApicast, OperatorApicastRequirements
from .selfmanaged import SelfManagedApicast, SelfManagedApicastRequirements
from .template import TemplateApicast, TemplateApicastRequirements
from .tls import TLSApicast, TLSApicastRequirements
