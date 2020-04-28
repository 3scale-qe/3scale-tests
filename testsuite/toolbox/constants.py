"These are constants used for Toolbox testing."

from dynaconf import settings

THREESCALE_SRC1 = settings['threescale']['admin']['url'].\
        replace('//', f"//{settings['threescale']['admin']['token']}@")

THREESCALE_DST1 = settings['toolbox']['destination_endpoint'].\
    replace('//', f"//{settings['toolbox']['destination_provider_key']}@")

# SERVICE_CMP_ATTRS = ('name', 'state', 'end_user_registration_required', 'backend_version',
#         'deployment_option', 'support_email',)
#
# PROXY_CONFIG_CMP_ATTRS = ('environment')
#
# PROXY_CONFIG_CONTENT_CMP_ATTRS = (
#   'name', 'oneline_description', 'description',
#   'txt_api', 'txt_support', 'txt_features', 'logo_file_name',
#   'logo_content_type', 'logo_file_size', 'state', 'intentions_required',
#   'draft_name', 'infobar', 'terms', 'display_provider_keys',
#   'tech_support_email', 'admin_support_email', 'credit_card_support_email',
#   'buyers_manage_apps', 'buyers_manage_keys', 'custom_keys_enabled',
#   'buyer_plan_change_permission', 'buyer_can_select_plan',
#   'notification_settings', 'default_application_plan_id',
#   'default_service_plan_id', 'default_end_user_plan_id',
#   'end_user_registration_required', 'system_name', 'backend_version',
#   'mandatory_app_key', 'buyer_key_regenerate_enabled', 'support_email',
#   'referrer_filters_required', 'deployment_option',
#   'kubernetes_service_link', 'proxiable?', 'backend_authentication_type',
# )
#
# PROXY_CONFIG_CONTENT_PROXY_CMP_ATTRS = (
#   'deployed_at', 'api_backend', 'auth_app_key', 'auth_app_id',
#   'auth_user_key', 'credentials_location', 'error_auth_failed',
#   'error_auth_missing', 'error_status_auth_failed', 'error_headers_auth_failed',
#   'error_status_auth_missing', 'error_headers_auth_missing', 'error_no_match',
#   'error_status_no_match', 'error_headers_no_match', 'hostname_rewrite',
#   'oauth_login_url', 'api_test_path', 'api_test_success',
#   'apicast_configuration_driven', 'oidc_issuer_endpoint', 'authentication_method',
#   'hostname_rewrite_for_sandbox', 'endpoint_port', 'valid?',
#   'service_backend_version',
# )
#
# PROXY_POLICY_CHAIN_CMP_ATTRS = ('name', 'version')

# PROXY_RULES_CMP_ATTRS = [
#   :http_method, :pattern, :metric_system_name, :delta, :redirect_url, :parameters,
#   :querystring_parameters,
# ].freeze
#
# PROXY_CMP_ATTRS = [
#   :api_backend, :api_test_path, :auth_app_id, :auth_app_key, :auth_user_key,
#   :credentials_location, :error_auth_failed, :error_auth_missing,
#   :error_headers_auth_failed, :error_headers_auth_missing, :error_headers_no_match,
#   :error_no_match, :error_status_auth_failed, :error_status_auth_missing,
#   :error_status_no_match, :lock_version, :secret_token,
# ].freeze
#
# PROXY_POLICY_CMP_ATTRS = [
#   :name, :humanName, :description, :version, :enabled, :removable, :id,
# ].freeze

# name, system_name, friendly_name, unit, description
METRIC_CMP_ATTRS = {'created_at', 'id', 'links', 'updated_at', 'system_name'}

# name, system_name, friendly_name, description
METRIC_METHOD_CMP_ATTRS = {'created_at', 'id', 'links', 'updated_at'}

# pattern, http_method, delta
MAPPING_CMP_ATTRS = {'created_at', 'id', 'last', 'links', 'metric_id', 'position', 'updated_at'}

# name, system_name, description, private_endpoint
BACKEND_CMP_ATTRS = {'id', 'account_id', 'created_at', 'updated_at', 'links'}

# APP_PLANS_CMP_ATTRS = [
#   :name, :state, :setup_fee, :cost_per_month, :trial_period_days,
#   :cancellation_period, :default, :custom, :system_name,
#   :end_user_required,
# ].freeze
#
# PRICING_RULES_CMP_ATTRS = [
#   :cost_per_unit, :min, :max,
# ].freeze
#
# ACTIVEDOCS_CMP_ATTRS = [
#   :name, :description, :published, :skip_swagger_validations, :body,
# ].freeze
#
# APPLICATION_CMP_ATTRS = [
#   :state, :enabled, :end_user_required, :name, :description,
# ].freeze
