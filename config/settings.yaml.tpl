# vim: filetype=yaml

# default section/environment of globally applicable values
# all the values can be repeated/overwritten in other environments
default:
  skip_cleanup: false  # should we delete all the 3scale objects created during test?
  ssl_verify: true  # use secure connection checks, this requires all the stack (e.g. trusted CA)
  ignore_insecure_ssl_warning: false  # ssl_verify=false produces some warnings from requests/urllib
  threescale:  # now configure threescale details
    version: "{DEFAULT_THREESCALE_VERSION}"  # tested version used for example is some tests needs to be skipped
    service:
      backends:  # list of backend services for testing
        httpbin: https://httpbin.org:443
        echo-api: https://echo-api.3scale.net:443
  openshift:
    projects:
      threescale:
        name: "{DEFAULT_OPENSHIFT_THREESCALE_PROJECT}"
  rhsso:
      test_user:
        username: testUser
        password: testUser


# dynaconf uses development environment by default
development:
  threescale:
    admin:
      url: https://3scale-admin.{DEVELOPMENT_THREESCALE_SUPERDOMAIN}
    master:
      url: https://master.{DEVELOPMENT_THREESCALE_SUPERDOMAIN}
    service:
      backends:
        primary: https://httpbin.{DEVELOPMENT_TESTENV_DOMAIN}:443
  rhsso:
    url: http://sso-testing-sso.{DEVELOPMENT_TESTENV_DOMAIN}
  openshift:
    servers:
      default:
        server_url: "{DEVELOPMENT_OPENSHIFT_URL}"
  redis:
    url: redis://apicast-testing-redis:6379/1
aws:
  threescale:
    admin:
      url: https://3scale-admin.{AWS_THREESCALE_SUPERDOMAIN}
    master:
      url: https://master.{AWS_THREESCALE_SUPERDOMAIN}
    service:
      backends:
        primary: https://httpbin.{AWS_TESTENV_DOMAIN}:443
  rhsso:
      url: http://sso-sso.apps.{AWS_TESTENV_DOMAIN}
  openshift:
    servers:
      default:
        server_url: "{AWS_OPENSHIFT_URL}"
    projects:
      threescale:
        name: "{AWS_OPENSHIFT_THREESCALE_PROJECT}"
