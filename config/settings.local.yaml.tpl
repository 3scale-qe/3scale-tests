# vim: filetype=yaml
# Example template to create local configuration with custom environment
# envsubst can be used to fill this

development:  # default dynaconf env
  threescale:
    version: "${THREESCALE_VERSION}"
    apicast_opearator_version: "${APICAST_OPERATOR_VERSION}"
    superdomain: ${THREESCALE_SUPERDOMAIN}
    admin:
      url: ${ADMIN_URL}
      username: ${ADMIN_USER}
      password: ${ADMIN_PASSWORD}
      token: ${ADMIN_ACCESS_TOKEN}
    master:
      url: ${MASTER_URL}
      username: ${MASTER_USER}
      password: ${MASTER_PASSWORD}
      token: ${MASTER_ACCESS_TOKEN}
    gateway:
      TemplateApicast:
        image: ${APICAST_IMAGE}
    service:
      backends:
        echo_api: https://${ECHO_API_HOSTNAME}:443
        httpbin_go: https://${GO_HTTPBIN_HOSTNAME}:443
        httpbin: https://${HTTPBIN_HOSTNAME}:443
        httpbin_nossl: http://${HTTPBIN_HOSTNAME}:80
  rhsso:
    url: http://${RHSSO_HOSTNAME}:80
    username: ${RHSSO_ADMIN}
    password: ${RHSSO_USERNAME}
  proxy:
    http: ${HTTP_PROXY}
    https: ${HTTP_PROXY}
  integration:
    service:
      proxy_service: ${FUSE_CAMEL_URL}
  fixtures:
    jaeger:
      config:
        reporter:
          localAgentHostPort: ${JAEGER_AGENT_URL}
        baggage_restrictions:
          hostPort: ${JAEGER_BAGGAGE_RESTRICTIONS_URL}
