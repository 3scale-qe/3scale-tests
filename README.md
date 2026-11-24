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

Backend APIs are referenced by service name in the settings, e.g. 'httpbin',
'httpbin_nossl'. These names are used (and kept unchanged) for historical
reason to avoid breaking of defined usage. In fact they don't represent
specific service, but rather an 'interface' of such service implemting its
calls.

### make tools

Container image can be built with script that provisions necessary
tools/services to openshift in tools project, `make tools` does the job. To
have it 100% functional a pull-secret is needed. There are two options to provide it.

Builtin and easier to use method is to use `use_dockerconfig` variable and
define config file (~/.docker/config is used by default):

```bash
DOCKERCONFIGJSON=/path/to/docker-config make tools use_dockerconfig=1
```

The other method is to create tools namespace and pull secret linked to
relevant service accounts in advance, e.g.:

```bash
oc create -f pull-secret.yaml -n tools
oc secrets link default pull-secret --for=pull -n tools
oc secrets link deployer pull-secret --for=pull -n tools
```

Pull secret should contain credentials to registries from which particular
images of tools are got. It is typically:

 * docker.io
 * quay.io
 * registry.redhat.io

Provisioning script(s) isn't part of codebase and it can be added just when
building the image!

### config/.secrets.yaml

**BEWARE!** If you are not blessed person with access to encrypted
`config/.secrets.yaml` you must delete it, otherwise nothing will work.

### Clone the Repo

Actually this should be pretty first step:

```bash
$ git clone https://github.com/3scale-qe/3scale-tests.git
$ cd 3scale-tests
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

 * docker.io/jaegertracing/all-in-one:latest
 * docker.io/jsmadis/go-httpbin:latest
 * docker.io/mailhog/mailhog:latest
 * docker.io/prom/prometheus
 * quay.io/mganisin/mockserver:latest
 * quay.io/rh_integration/3scale-fuse-camel-proxy:latest
 * quay.io/3scale/echoapi:stable
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

`make speedrun NAMESPACE=3scale`
 - this is 'test' just even more reduced to provide better coverage than smoke but still fast enough

`make flaky NAMESPACE=3scale`
 - unstable tests causing false alarms

`make disruptive NAMESPACE=3scale`
 - tests with side-effect

`make capabilities-smoke NAMESPACE=3scale`
 - smoke tests using 3scale Capabilities client instead of 3scale API client

`make capabilities-speedrun NAMESPACE=3scale`
 - speedrun tests using 3scale Capabilities client instead of 3scale API client

Targets can be combined

`make test flaky NAMESPACE=3scale`
 - to run general tests together with flaky

`make -k test flaky NAMESPACE=3scale`
 - to ensure flaky is executed even if general test ends with failure

`make ./testsuite/tests/apicast/auth/test_basic_auth_user_key.py NAMESPACE=3scale`
 - to run particular test standalone

### 3scale Capabilities

By default 3scale REST API client is used. 3scale Capabilities client can be used
instead of 3scale REST API client by using `--capabilities` argument. This argument
unlock running of specific Capabilities tests. For more information about 3scale Capabilities
see https://github.com/3scale/3scale-operator/blob/master/doc/operator-application-capabilities.md

### Test Selection, Marks and Custom Arguments

Selection of tests in the targets described above is based on pytest marks and
extra commandline options. Marks should be used wisely and reviewed carefully
and extra care is required when combining marks on one test. For example
`pytest.mark.disruptive` on some UI test causes that neither `make ui` nor
`make disruptive` without extra option runs such test. This danger applies to
selections based on the arguments, e.g. `pytest.mark.flaky` is safe to combine
with anything, it just doesn't have to be reasonable for every case.

### Behavior of warn_and_skip

Some tests and/or fixture use `warn_and_skip` function to skip the test in case
of missing preconditions. There is a mechanism to control behavior of
`warn_and_skip`. By default `warn_and_skip` prints warning with given message
and also skips the test(s) with same message. If `warn_and_skip:` section is
defined in settings, this is used to modify default behavior. Possible options
are 'quiet', 'warn', 'fail'. The option 'warn' is identical to default, the
option 'quiet' skips the test(s) but doesn't print warning and the option
'fail' makes the test(s) fail entirely. This is helpful if some tests shouldn't
be overlooked. The settings could look like this:

```
  warn_and_skip:
    testsuite/tests/prometheus: quiet
    testsuite/tests/apicast/parameters: fail
```

This does not provide adjustement on level of particular tests. In theory it
does, however if `warn_and_skip` is used in fixture, then all the tests within
the scope of the fixture behave like first test. E.g. `prometheus` fixture is
session scoped, therefore all prometheus test will share same setting.

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

### test-in-docker

There is special make target that runs the test in docker/podman/container and
spins up also selenium as sidecar. Basic usage is straightforward, to run smoke
tests:

`NAMESPACE=3scale make test-in-docker`

This target promotes all `_3SCALE_TESTS_*` env variables to the container.

`$KUBECONFIG` and `$resultsdir` are mounted. To ensure process within the
container has correct permissions to these files current userid is preserved
inside the container. This should work unless remapping of userids is
customized As this feature has to be enabled explicitly person who did this
should know how to deal with that.

By default `$resultsdir` is set to current dir. It is good idea to create
dedicated directory for results and set `$resultsdir` accordingly.

This target runs command `docker`, podman can be used with appropriate symlink.

`SECRETS_FOR_DYNACONF` is also promoted to the image and it is preset to
`config/.secrets.yaml` by default if that file is present, otherwise
`config/settings.local.yaml` is set. If `config/.secrets.yaml` exists it must
be valid (unencrypted) and it is only config bound to the image. Set the
variable to force `config/settings.local.yaml` or anything else:

`SECRETS_FOR_DYNACONF=$PWD/config/settings.local.yaml NAMESPACE=3scale make test-in-docker`

Variable `cmd` can be used to alter command for the container, to run ui tests:

`NAMESPACE=3scale make test-in-docker cmd=ui`

Env variable `flags` is also promoted to the container, this works as expected:

`NAMESPACE=3scale make test-in-docker flags=--ui`

Variable `image` can be set to use custom image:

`make container-image`
`NAMESPACE=3scale make test-in-docker image=3scale-tests`

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
Refer to [CONTRIBUTING.md](CONTRIBUTING.md)
