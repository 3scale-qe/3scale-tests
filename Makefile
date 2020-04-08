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

test: ## Run test
test: pytest tests

debug: ## Run test  with debug flags
debug: flags := $(flags) -s
debug: test

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

container-image: ## Build container image
	docker build -t 3scale-py-testsuite .

clean: ## clean pip deps
	rm -f Pipfile.lock .make-*
	-pipenv --rm

# Check http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
help: ## Print this help
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
