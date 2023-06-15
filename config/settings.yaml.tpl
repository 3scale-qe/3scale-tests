# vim: filetype=yaml

# default section/environment of globally applicable values
# all the values can be repeated/overwritten in other environments
default:
  skip_cleanup: false  # should we delete all the 3scale objects created during test?
  ssl_verify: true  # use secure connection checks, this requires all the stack (e.g. trusted CA)
  http2: false # enables http/2 requests to apicast
  tester: whatever # used to create unique names for 3scale artifacts it defaults to whoami or uid
  threescale:  # now configure threescale details
    version: "{DEFAULT_THREESCALE_VERSION}"  # tested version used for example is some tests needs to be skipped
    apicast_operator_version: "{DEFAULT_APICAST_OPERATOR_VERSION}"  # version of apicast operator used for example is some tests needs to be skipped
    superdomain: "{DEFAULT_THREESCALE_SUPERDOMAIN}"  # Threescale superdomain/wildcard_domain
    service:
      backends:  # list of backend services for testing
        httpbin: https://httpbin.org:443
        echo_api: https://echo-api.3scale.net:443
        httpbin_nossl: http://httpbin.org:80
    gateway:  # More info at GATEWAYS.md
      default:
        kind: "SystemApicast"
        openshift:  # Only needed if run without OpenShift
          project_name: "{DEFAULT_OPENSHIFT_THREESCALE_PROJECT}"
          kind: "OpenShiftClient"
      WASMGateway:
        image: "{WASM_IMAGE}"  # wasm image build for pulling
        pull_secret: "{PULL_SECRET}"  # name of pull secret resource in same namespace as httpbin
        httpbin:
          project_name: "{HTTPBIN_NAMESPACE}"
          kind: "OpenShiftClient"
        mesh:
          project_name: "{SERVICE_MESH_NAMESPACE}"
          kind: "OpenShiftClient"
  openshift:
    servers:
      default:
        server_url: "{DEFAULT_OPENSHIFT_URL}"
    projects:
      threescale:
        name: "{DEFAULT_OPENSHIFT_THREESCALE_PROJECT}"
  rhsso:
    test_user:
      username: testUser
      password: testUser
  proxy:
    # http proxy settings
    http: http://tinyproxy-service.tiny-proxy.svc:8888
    https: http://tinyproxy-service.tiny-proxy.svc:8888
  reporting:
    print_app_logs: true # whether to print application logs during testing
    title: Brief Description # custom title used for junit/polarion reporting
    testsuite_properties:
      polarion_project_id: PROJECTID
      polarion_response_myteamsname: teamname
  fixtures:
    threescale:
      private_tenant: False  # if true standalone tenant is created to run all the tests
    jaeger:
      url: "" # route to the jaeger-query service for the querying of traces
      config:
        reporter:
          localCollectorHostPort: "" # url to the jaeger-collector (only hostname and port is parsed, may be internal)
        baggage_restrictions:
          hostPort: "" # route to the jaeger-query (may be internal)
    ui:
      browser:
        source: "" #local ,remote or binary
        webdriver: "" #chrome , firefox or edge(edge with remote drivers)
        remote_url: "" #URL and port to remote selenium instance e.g. http://127.0.0.1:4444
    tools:
      # tools is a fixture to provide testenv services like echo_api, jaeger
      # and services that are needed for testing each service is identified by
      # a key, for compatibility reasons some keys are predefined as they have
      # been user in threescale:services:backends of this config, furthermore
      # the tools read from config are searched there as well. OpenshiftProject
      # implementation inroduced route based keys and some special key to add
      # extra information. so 'httpbin+https' returns https:// url based on
      # route to httpbin. There is also logic to define openshift service url
      # e.g. 'httpbin+svc:8888' returns 'httpbin.{tools-namespace}.svc:8888
      # This logic makes the computation on its own and such option does not
      # have to be defined in the config. However can be in this config as
      # well. In that case, obviously the value has to be defined explicitly.
      # Such key with '+' and ':' can not be defined as env variable therefore
      # if `httpbin+svc:8888` is not found also `httpbin_plus_svc_port_8888` is
      # searched, this latter key can be used also in the config, however it
      # should not be, this is just for env.
      sources: [ Rhoam, OpenshiftProject, Settings ] # Testenv information sources ordered by priority, query ends at first return of some value
      namespace: tools # openshift namespace/project where the testenv tools are deployed
    private_base_url:
      default: echo_api # tool name to be used by default for backend
  warn_and_skip:
    # section to control how warn_and_skip should behave for particular tests
    # works just for tests and fixture that use warn_and_skip
    # doesn't provide granularity on test level, if used in fixtures, affects
    # all the tests from same scope of the fixture.
    # Best match is chosen
    # possible values: quiet, warn, fail; default: warn
    testsuite: warn
    testsuite/tests/prometheus: quiet
    testsuite/tests/apicast/parameters: fail


# dynaconf uses development environment by default
development:
  threescale:
    admin:
      url: https://3scale-admin.{DEVELOPMENT_THREESCALE_SUPERDOMAIN}
      token: "{DEVELOPMENT_ADMIN_ACCESS_TOKEN}"
      username: admin
      password: "{DEVELOPMENT_ADMIN_PASSWORD}"
    master:
      url: https://master.{DEVELOPMENT_THREESCALE_SUPERDOMAIN}
      token: "{DEVELOPMENT_MASTER_ACCESS_TOKEN}"
      username: master
      password: "{DEVELOPMENT_MASTER_PASSWORD}"
    service:
      backends:
        primary: https://httpbin.{DEVELOPMENT_TESTENV_DOMAIN}:443
        httpbin_go: https://httpbingo.{DEVELOPMENT_TESTENV_DOMAIN}:443
        httpbin_go_mtls: https://httpbingo-mtls.{DEVELOPMENT_TESTENV_DOMAIN}:443
      projects:
        # Project which the secrets containing the certificates for mtls resides in.
        # Usually the secrets are created in httpbin project because htttpbin go with mtls is deployed in there.
        mtls-certificates:
          name: httpbin

  auth0:
      client: "" # Auth0 client id
      client-secret: "" # Auth0 client secret
      domain: "" # Domain URL to Auth0 page
  rhsso:
    # admin credentials
    username: "{DEFAULT_RHSSO_ADMIN_USERNAME}"
    password: "{DEFAULT_RHSSO_ADMIN_PASSWORD}"
    url: http://sso-testing-sso.{DEVELOPMENT_TESTENV_DOMAIN}
  openshift:
    projects:
      threescale:
        name: "{DEVELOPMENT_OPENSHIFT_THREESCALE_PROJECT}"
    servers:
      default:
        server_url: "{DEVELOPMENT_OPENSHIFT_URL}"
  redis:
    url: redis://apicast-testing-redis:6379/1
  prometheus:
    url: "{PROMETHEUS_URL}"
  toolbox:
    # rpm/gem/podman; rpm = command from rpm package, gem = command from gem
    # 'ruby_version' should be defined for "gem" option
    # 'podman_image' should be defined for "podman" option
    # 'podman_cert_dir' should be defined for "podman" option
    # 'destination_endpoint' url to destination 3scale api, if empty new tenant is created
    # 'destination_provider_key' personal access key for destination tenant/3scale with rw to all scopes
    # cmd: "rpm"
    # cmd: "gem"
    # ruby_version: "rh-ruby24"
    local_client: false  # if true run the command locally not via ssh
    cmd: "podman"
    podman_cert_dir: "/var/data"
    podman_cert_name: "ca-bundle.crt"
    destination_endpoint: "" # url to 3scale api
    destination_provider_key: "" # token
    machine_ip: "" # where the container is
    ssh_user: "" # user at the machine where the container is
    ssh_passwd: "" # password for above user
    podman_image: "" # container image ID
  hyperfoil:
    url: "" # URL for hyperfoil controller
  cfssl:
    binary: "cfssl" # Path to the cfssl binary
  images:
    apicast:
      manifest_digest: # Multi-arch manifest digest
      resolved_images: # Dict of resolved images
        amd64:
        ppc64le:
        s390x:
    apicast_operator: # Multi-arch manifest digest
    threescale_backend:
      manifest_digest: # Multi-arch manifest digest
      resolved_images: # Dict of resolved images
        amd64:
        ppc64le:
        s390x:
    threescale_memcached:
      manifest_digest: # Multi-arch manifest digest
      resolved_images: # Dict of resolved images
        amd64:
        ppc64le:
        s390x:
    threescale_system:
      manifest_digest: # Multi-arch manifest digest
      resolved_images: # Dict of resolved images
        amd64:
        ppc64le:
        s390x:
    threescale_zync:
      manifest_digest: # Multi-arch manifest digest
      resolved_images: # Dict of resolved images
        amd64:
        ppc64le:
        s390x:
    threescale_operator: # Multi-arch manifest digest
