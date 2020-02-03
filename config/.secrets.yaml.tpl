# vim: filetype=yaml
default:
  rhsso:
    username: "{DEFAULT_RHSSO_ADMIN_USERNAME}"
    password: "{DEFAULT_RHSSO_ADMIN_PASSWORD}"


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
        primary: https://httpbin.{DEVELOPMENT_TESTENV_DOMAIN}
  openshift:
    projects:
      threescale:
        name: "{DEVELOPMENT_OPENSHIFT_THREESCALE_PROJECT}"
    servers:
      default:
        server_url: "{DEVELOPMENT_OPENSHIFT_SERVER}"
  rhsso:
    url: http://sso-testing-sso.{DEVELOPMENT_TESTENV_DOMAIN}
