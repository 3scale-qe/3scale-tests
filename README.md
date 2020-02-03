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
### Creating your personal secrets file 

Create a secrets file in the `config` directory from the secrets file template `.secrets.yaml.tpl`.

```
$ cp config/.secrets.yaml.tpl config/.secrets.yaml
```

Edit your `.secrets.yaml` using you preferred editor by following the instructions on it.

### Run the tests

Testsuite is using the ``pytest`` as a testing framework, so to run all the tests,
we can use just:

```bash
$ pipenv run ./run-testsuite
```

## Contribute
Refer to [CONTRIBUTE.md]
