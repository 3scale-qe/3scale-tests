# 3scale Test Suite in the Python

This is testsuite by 3scale QE implemented in the Python

## Use the suite
Here are the prerequisites to use the test suite.

### Required tools
To be able to use the suite correctly you need to install all the dependencies.
Suite is using the [pipenv](https://github.com/pypa/pipenv) to manage dependencies
defined in the `Pipfile`.

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

BEWARE! ``config/.secrets.yaml`` contains sensitive data and it is encrypted
thus. Due to the encypryption the format is 'invalid' and dynaconf can't parse
the configuration properly. Either decrypt ``config/.secrets.yaml`` (``git crypt unlock``)
or delete the file and provide your own settings in ``config/settings.local.yaml``

### Run the tests

Testsuite is using the ``pytest`` as a testing framework, so to run all the tests,
we can use just:

```bash
$ pipenv run ./run-testsuite
```

## Contribute
Refer to [CONTRIBUTE.md]
