# vim: filetype=yaml
# Example template to create local ocnfiguration with custom environment
# envsubst can be used to fill this

${ENVIRONMENT}:
  threescale:
    version: "${THREESCALE_VERSION}"
    admin:
      url: https://3scale-admin.${THREESCALE_SUPERDOMAIN}
      # token doesn't have to be specified explicitly unless intended
      # token: "${ADMIN_ACCESS_TOKEN}"
    service:
      backends:
        primary: https://httpbin.${TESTENV_DOMAIN}
  openshift:
    servers:
      default:
        server_url: "${OPENSHIFT_SERVER}"
    projects:
      threescale:
        name: "${OPENSHIFT_THREESCALE_PROJECT}"
