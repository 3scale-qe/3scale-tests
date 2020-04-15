# 3scale Test Suite in the Python

This is testsuite by 3scale QE implemented in the Python

## Use the suite
Here are the prerequisites to use the test suite.

### Required tools
To be able to use the suite correctly you need to install all the dependencies.
Suite is using the [pipenv](https://github.com/pypa/pipenv) to manage dependencies
defined in the `Pipfile`.

Openshift client and logged to the correct cluster.

### Get the suite and install dependencies

To get the suite you you can use `git clone`:
```bash
$ git clone git@gitlab.cee.redhat.com:3scale-qe/3scale-py-testsuite.git
```

then get to the test suite directory:
```bash
$ cd 3scale-py-testsuite
```

after that you can install dependencies using the pipenv
```bash
$ pipenv install --dev
```


### Customize the configuration

Default configuration is stored in ``config/settings.yaml`` and
``config/.secrets.yaml``. These files are supposed to be unchanged. To modify
the configuration use config/settings.local.yaml file that will override the
defaults. Consult ``config/settings.yaml.tpl`` for possible options.

**BEWARE!*** ``config/.secrets.yaml`` contains sensitive data and it is
encrypted thus. Due to the encypryption the format is 'invalid' and dynaconf
can't parse the configuration properly. Either decrypt ``config/.secrets.yaml``
(``git crypt unlock``) or delete the file and provide your own settings in
``config/settings.local.yaml``


### Run the tests

#### Before running

1) Need to be logged on openshift `oc login`
2) 3scale platform **is not deployed** within the test, so a valid instalation
on a project is needed. This can be set on
`config/.secrets.local#development.openshift.projects.threescale.name`
3) Need to check that the `system-seed` secret is correctly created in the
project
```
oc get secret system-seed -o yaml -n ${PROJECT}
```

#### Running
Testsuite is using the ``pytest`` as a testing framework, so to run all the tests,
we can use just:

```bash
$ pipenv run ./run-testsuite
```

Or `make test` can be used



### Test options

#### Environment variables:

These variables are to enable/disable some testsuite options:

- **_3SCALE_TESTS_IGNORE_INSECURE_SSL_WARNING(bool, default: true)**: To disable Insecure SSL warning
- **_3SCALE_TESTS_SSL_VERIFY**(bool): To not verify SSL certs


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
Refer to [CONTRIBUTE.md]
