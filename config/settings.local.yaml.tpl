# vim: filetype=yaml
# Example template to create local ocnfiguration with custom environment
# envsubst can be used to fill this

${ENVIRONMENT}:
  threescale:
    version: "${THREESCALE_VERSION}"
    # url & token doesn't have to be specified explicitly unless intended
    # in such case login to openshift is a must
    # admin:
      # url: https://3scale-admin.${THREESCALE_SUPERDOMAIN}
      # token: "${ADMIN_ACCESS_TOKEN}"
    service:
      backends:
        primary: https://httpbin.${TESTENV_DOMAIN}:443
        httpbin-go: https://httpbingo.${TESTENV_DOMAIN}:443
  rhsso:
    # admin credentials
    username: "${RHSSO_ADMIN_USERNAME}"
    password: "${RHSSO_ADMIN_PASSWORD}"
  openshift:
    servers:
      default:
        server_url: "${OPENSHIFT_URL}"
    projects:
      threescale:
        name: "${OPENSHIFT_THREESCALE_PROJECT}"
