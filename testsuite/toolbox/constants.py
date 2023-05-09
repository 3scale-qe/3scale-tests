"These are constants used for Toolbox testing."

# 'name', 'state', 'end_user_registration_required', 'backend_version',
# 'deployment_option', 'buyer_can_select_plan',
# 'buyer_key_regenerate_enabled', 'buyer_plan_change_permission',
# 'buyers_manage_apps', 'buyers_manage_keys', 'custom_keys_enabled','intentions_required',
# 'mandatory_app_key', 'referrer_filters_required'
SERVICE_CMP_ATTRS = {"created_at", "id", "links", "system_name", "support_email", "updated_at"}

# 'admin_support_email', 'backend_authentication_type', 'backend_version',
# 'buyer_can_select_plan', 'buyer_key_regenerate_enabled', 'buyer_plan_change_permission',
# 'buyers_manage_apps', 'buyers_manage_keys', 'credit_card_support_email',
# 'custom_keys_enabled', 'default_application_plan_id', 'default_end_user_plan_id',
# 'default_service_plan_id', 'deployment_option', 'description', 'display_provider_keys',
# 'draft_name', 'end_user_registration_required', 'infobar', 'intentions_required',
# 'kubernetes_service_link', 'logo_content_type', 'logo_file_name', 'logo_file_size',
# 'mandatory_app_key', 'name', 'notification_settings', 'oneline_description', 'proxiable?',
# 'referrer_filters_required', 'state', 'system_name', 'tech_support_email',
# 'terms', 'txt_api', 'txt_features', 'txt_support'

PROXY_CONFIG_CONTENT_CMP_ATTRS = {
    "account_id",
    "backend_authentication_value",
    "created_at",
    "id",
    "proxy",
    "support_email",
    "tenant_id",
    "updated_at",
}

# 'api_backend', 'api_test_path', 'api_test_success', 'apicast_configuration_driven',
# 'auth_app_id', 'auth_app_key', 'auth_user_key', 'authentication_method',
# 'credentials_location', 'deployed_at', 'endpoint_port', 'error_auth_failed',
# 'error_auth_missing', 'error_headers_auth_failed', 'error_headers_auth_missing',
# 'error_headers_limits_exceeded', 'error_headers_no_match', 'error_limits_exceeded',
# 'error_no_match', 'error_status_auth_failed', 'error_status_auth_missing',
# 'error_status_limits_exceeded', 'error_status_no_match', 'hostname_rewrite',
# 'hostname_rewrite_for_sandbox', 'jwt_claim_with_client_id', 'jwt_claim_with_client_id_type',
# 'oauth_login_url', 'oidc_issuer_endpoint', 'oidc_issuer_type', 'service_backend_version',
# 'valid?'
PROXY_CONFIG_CONTENT_PROXY_CMP_ATTRS = {
    "backend",
    "created_at",
    "endpoint",
    "hosts",
    "id",
    "lock_version",
    "policy_chain",
    "production_domain",
    "proxy_rules",
    "sandbox_endpoint",
    "secret_token",
    "service_id",
    "staging_domain",
    "tenant_id",
    "updated_at",
}

# 'delta', 'http_method', 'last', 'owner_type', 'parameters', 'pattern', 'position',
# 'querystring_parameters', 'redirect_url'
PROXY_RULES_CMP_ATTRS = {
    "created_at",
    "id",
    "metric_id",
    "metric_system_name",
    "owner_id",
    "proxy_id",
    "tenant_id",
    "updated_at",
}

# 'api_test_path', 'auth_app_id', 'auth_app_key', 'auth_user_key', 'credentials_location',
# 'deployment_option', 'error_auth_failed', 'error_auth_missing', 'error_headers_auth_failed',
# 'error_headers_auth_missing', 'error_headers_limits_exceeded', 'error_headers_no_match',
# 'error_limits_exceeded', 'error_no_match', 'error_status_auth_failed',
# 'error_status_auth_missing', 'error_status_limits_exceeded', 'error_status_no_match',
# 'lock_version', 'oidc_issuer_endpoint', 'oidc_issuer_type', 'secret_token'

PROXY_CMP_ATTRS = {
    "api_backend",
    "created_at",
    "endpoint",
    "links",
    "lock_version",
    "policies_config",
    "sandbox_endpoint",
    "service_id",
    "updated_at",
}

# name, system_name, friendly_name, unit, description
METRIC_CMP_ATTRS = {"created_at", "id", "links", "updated_at", "system_name", "parent_id"}

# name, system_name, friendly_name, description
METRIC_METHOD_CMP_ATTRS = {"created_at", "id", "links", "parent_id", "updated_at"}

# pattern, http_method, delta
MAPPING_CMP_ATTRS = {"created_at", "id", "last", "links", "metric_id", "position", "updated_at"}

# name, system_name, description, private_endpoint
BACKEND_CMP_ATTRS = {"id", "account_id", "created_at", "updated_at", "links"}

# 'approval_required', 'cancellation_period', 'cost_per_month', 'custom', 'default',
# 'name', 'setup_fee', 'state', 'system_name', 'trial_period_days'
APP_PLANS_CMP_ATTRS = {"created_at", "id", "links", "updated_at"}

# 'period', 'value'
LIMITS_CMP_ATTR = {"id", "metric_id", "plan_id", "created_at", "updated_at", "links"}

# 'cost_per_unit', 'min', 'max'
PRICING_RULES_CMP_ATTRS = {"id", "metric_id", "created_at", "updated_at", "links"}

# 'system_name', 'name', 'description', 'published', 'skip_swagger_validations', 'body'
ACTIVEDOCS_CMP_ATTRS = {"id", "service_id", "created_at", "updated_at"}

# 'path'
BACKEND_USAGES_CMP_ATTRS = {"id", "service_id", "backend_id", "links"}

# 'description', 'enabled', 'end_user_required', 'name', 'provider_verification_key',
# 'state', 'user_key'

APPLICATION_CMP_ATTRS = {
    "account_id",
    "created_at",
    "first_daily_traffic_at",
    "first_traffic_at",
    "id",
    "links",
    "plan_id",
    "provider_verification_key",
    "service_id",
    "updated_at",
}
