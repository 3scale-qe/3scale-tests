.PHONY: commit-acceptance pylint flake8 mypy all-is-package \
	pytest tests smoke junit \
	pipenv pipenv-dev \
	container-image \
	clean

commit-acceptance: pylint flake8 mypy all-is-package

pylint flake8 mypy: pipenv-dev
	pipenv run $@ $(flags) testsuite

all-is-package:
	@echo
	@echo "Searching for dirs missing __init__.py"
	@! find testsuite/ -type d \! -name __pycache__ \! -exec test -e {}/__init__.py \; -print | grep '^..*$$'

pytest tests: pipenv
	pipenv run python -m pytest $(flags) testsuite

smoke: pipenv
	pipenv run python -m pytest -n 6 -m smoke $(flags) testsuite

junit: pipenv
	pipenv run python -m pytest --junitxml=junit.xml $(flags) testsuite

Pipfile.lock: Pipfile
	pipenv lock

.make-pipenv-sync: Pipfile.lock
	pipenv sync
	touch .make-pipenv-sync

.make-pipenv-sync-dev: Pipfile.lock
	pipenv sync --dev
	touch .make-pipenv-sync-dev .make-pipenv-sync

pipenv: .make-pipenv-sync

pipenv-dev: .make-pipenv-sync-dev

container-image:
	docker build -t 3scale-py-testsuite .

clean:
	rm -f Pipfile.lock .make-*
	-pipenv --rm
