# 3scale Test Suite in the Python

This is testsuite by 3scale QE implemented in the Python

## Before You Run It

### Software Requirements

The first thing that should be installed is [pipenv](https://github.com/pypa/pipenv).
[Pipenv](https://github.com/pypa/pipenv) is essential tool necessary to run the
testsuite. You will also have to install all the packages from [REQUIRES](REQUIRES).
Double check that ALL of those packages have been successfully installed!
This file ([REQUIRES](REQUIRES)) references packages as they are known in redhat 
based distributions. For other distros please make sure equivalent is present.

### Openshift Login

The testsuite assumes already authorized session to the openshift with 3scale
deployed. This can be avoided with proper configuration, however easiest and
most convenient way is to have the session. The way through configuration is
dedicated to special use cases.

### 3scale Deployed

The testsuite doesn't install 3scale itself, besides `oc login` have also
3scale deployed.

The testsuite attempts to read many options from `system-seed` secret. This
standard part of 3scale deployment, so it is unexpected that it is not present.
Anyway in case of troubles this can be the cause. Everything gathered there can
be explicitly set in the configuration to omit it.

### Backend APIs/Services

Obviously some backend behind 3scale is needed for testing. Default
configuration points to some publicly available services. However it is
**highly desirable** to deploy own instance(s) of suitable service and change
configuration to use this (through `config/settings.local.yaml`

### config/.secrets.yaml

**BEWARE!** If you are not blessed person with access to encrypted
`config/.secrets.yaml` you must delete it, otherwise nothing will work.

### Clone the Repo

Actually this should be pretty first step:

```bash
$ git clone git@gitlab.cee.redhat.com:3scale-qe/3scale-py-testsuite.git
$ cd 3scale-py-testsuite
```

## Customize the Configuration

The testsuite uses [dynaconf](https://dynaconf.readthedocs.io/) to manage the
configurtion

Default ocnfiguration is sufficient to run basic set of tests.

Default configuration is stored in `config/settings.yaml` and
`config/.secrets.yaml`. These files are supposed to be unchanged. To modify the
configuration use `config/settings.local.yaml` file that will override the
defaults. Consult [settings.yaml.tpl](config/settings.yaml.tpl) for possible
options.

As mentioned above `config/.secrets.yaml` is encrypted file. It has to be
either unlocked with `git crypt unlock` or deleted.

#### Environment Variables:

It's feature of dynaconf that all the options can be set also via environment
variables. All the options begin with `_3SCALE_TESTS_*` prefix. Please refer to
the [documentation](https://dynaconf.readthedocs.io/) of dynaconf for more
details.

Keep in mind that env variable handling in dynaconf is (partially) case
sensitive, rather always follow (lower)case from the config file.

These variables are to enable/disable some testsuite options:

- `_3SCALE_TESTS_ssl_verify(bool)`: To not verify SSL certs

## Required Services

To run all the tests various services must be deployed. If mentioned services
are deployed in `tools` namespace (name can be changed in config) on same
openshift, then they are auto-discovered, otherwise they have to be properly
set in configuration.

Here is the list of services:

 * docker.io/eloycoto/apicast:tinyproxy
 * docker.io/jaegertracing/all-in-one:latest
 * docker.io/jsmadis/echo-api:latest
 * docker.io/jsmadis/go-httpbin:latest
 * docker.io/jsmadis/httpbin:latest
 * docker.io/mailhog/mailhog:latest
 * docker.io/prom/prometheus
 * docker.io/sxmichael/requestbin:latest
 * quay.io/rh_integration/3scale-fuse-camel-proxy:latest
 * registry.redhat.io/rhscl/redis-32-rhel7:3.2
 * registry.redhat.io/rh-sso-7/sso74-openshift-rhel8:7.4

## Run the Tests

Testsuite is using the `pytest` as a testing framework, couple of `make`
targets are ready for easier execution. The openshift project/namespace of
3scale deployment should be always defined as variable `NAMESPACE`.
Alternatively it can be set in the configuration.

`make smoke NAMESPACE=3scale`
 - smoke tests, short in count, quick in execution

`make test NAMESPACE=3scale`
 - general way to run the testsuite; troublesome tests excluded == no flaky or disruptive

`make flaky NAMESPACE=3scale`
 - unstable tests causing false alarms

`make disruptive NAMESPACE=3scale`
 - tests with side-effect

Targets can be combined

`make test flaky NAMESPACE=3scale`
 - to run general tests together with flaky

`make -k test flaky NAMESPACE=3scale`
 - to ensure flaky is executed even if general test ends with failure

`make ./testsuite/tests/apicast/auth/test_basic_auth_user_key.py NAMESPACE=3scale`
 - to run particular test standalone

### pytest Arguments

The arguments to pytest can be passed as `flags=` variable:

`make smoke NAMESPACE=3scale flags=--junitxml=junit.xml`

## Run the tests in container

Assuming the container is called `3scale-py-testsuite` the docker command is:

```
docker run \
	-v $HOME/.kube/config:/opt/kubeconfig:z \
	-v $PWD/config/settings.local.yaml:/opt/settings.local.yaml:z \
	-v $PWD/results:/test-run-results:z \
	-e KUBECONFIG=/opt/kubeconfig \
	-e SECRETS_FOR_DYNACONF=/opt/settings.local.yaml \
	-e NAMESPACE=3scale \
	3scale-py-testsuite
```

 * `/test-run-results` is container directory where all the results are stored
 * `$KUBECONFIG` is highly recommended as much less configruration is needed
 * `$SECRETS_FOR_DYNACONF` and relevant bind provide way how pass extra configuration
 * `$NAMESPACE` with project name where 3scale is installed

Without any args smoke tests are executed. Any arg as for `make` from examples
above can be passed to run appropriate set.

## Debugging

### Local mode

When running on local mode, an interactive debugger can be launched. To launch
the execution with debugger capabilities `make debug` can be used, or you can
add the `-s` flag on pytest.

To stop the execution on specific point, the following statement can be added in
the code:

```
import ipdb; ipdb.set_trace()
```

Whe execution reach the tracepoint, it will launch a IPython shell where data
can be checked.


### Remote mode:
TBD

## Contribute
Refer to [CONTRIBUTE.md](CONTRIBUTE.md)
