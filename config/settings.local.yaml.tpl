# vim: filetype=yaml
# Example template to create local configuration with custom environment
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
        httpbin_go: https://httpbingo.${TESTENV_DOMAIN}:443
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
  proxy:
    # http proxy settings
    http: http://tinyproxy-service.tiny-proxy.svc:8888
    https: http://tinyproxy-service.tiny-proxy.svc:8888
  toolbox:
    destination_endpoint: "" # url to 3scale api
    destination_provider_key: "" # token
    machine_ip: "" # where the container is
    ssh_user: "" # user at the machine where the container is
    ssh_passwd: "" # password for above user
    podman_image: "" # container image ID
  fixtures:
    jaeger:
      url: "" # route to the jaeger-query service for the querying of traces
      config:
        reporter:
            localAgentHostPort: "" # route to the jaeger-agent (may be internal)
        baggage_restrictions:
            hostPort: "" # route to the jaeger-query (may be internal)
    apicast:
      parameters:
        modular_apicast:
          amp_release: "" # tag of the image stream, "master" for nightlies,
                          # 3scale version otherwise
    ui:
      browser:
        provider: "" #local or remote
        webdriver: "" #chrome or firefox
  hyperfoil:
    url: "" # URL for hyperfoil controller
    shared_template: #template that will be added to each hyperfoil benchmark definition
  cfssl:
    binary: "cfssl" # Path to the cfssl binary