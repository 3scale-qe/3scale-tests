.PHONY: quality-check lint pylint flake8 mypy all-is-package pytest tests clean commit-acceptance run configure configure-dev pipenv pipenv-dev container-image

commit-acceptance quality-check lint: pylint flake8 mypy all-is-package

pylint flake8 mypy: configure-dev
	pipenv run $@ $(flags) testsuite

all-is-package:
	@echo
	@echo "Searching for dirs missing __init__.py"
	@! find testsuite/ -type d \! -name __pycache__ \! -exec test -e {}/__init__.py \; -print | grep '^..*$$'

run tests pytest: configure
	pipenv run python -m pytest $(flags) testsuite

smoke: configure
	pipenv run python -m pytest -n 6 -m smoke $(flags) testsuite

junit:
	pipenv run python -m pytest --junitxml=junit.xml $(flags) testsuite

Pipfile.lock: Pipfile
	pipenv lock

.make-pipenv-sync: Pipfile.lock
	pipenv sync
	touch .make-pipenv-sync

.make-pipenv-sync-dev: Pipfile.lock
	pipenv sync --dev
	touch .make-pipenv-sync-dev .make-pipenv-sync

configure pipenv: .make-pipenv-sync

configure-dev pipenv-dev: .make-pipenv-sync-dev

container-image:
	docker build -t 3scale-py-testsuite .

clean:
	rm -f Pipfile.lock .make-*
	-pipenv --rm
