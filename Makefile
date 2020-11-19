.PHONY: commit-acceptance pylint flake8 mypy all-is-package \
	test pytest tests smoke junit \
	pipenv pipenv-dev \
	container-image \
	clean

TB ?= short
LOGLEVEL ?= INFO
resultsdir ?= .

ifdef junit
flags += --junitxml=$(resultsdir)/junit-$@.xml
endif

PYTEST = pipenv run python -m pytest --tb=$(TB)
RUNSCRIPT = pipenv run ./scripts/

commit-acceptance: pylint flake8 mypy all-is-package

pylint flake8 mypy: pipenv-dev
	pipenv run $@ $(flags) testsuite

all-is-package:
	@echo
	@echo "Searching for dirs missing __init__.py"
	@! find testsuite/ -type d \! -name __pycache__ \! -path 'testsuite/resources/*' \! -exec test -e {}/__init__.py \; -print | grep '^..*$$'

# pattern to run testfiles individually
%.py: FORCE
	$(PYTEST) $(flags) $@

test: ## Run test
test pytest tests: pipenv
	$(PYTEST) -m 'not flaky' $(flags) testsuite

debug: ## Run test  with debug flags
debug: flags := $(flags) -s
debug: test

smoke: pipenv
	$(PYTEST) -n6 -msmoke $(flags) testsuite

flaky: pipenv
	$(PYTEST) -mflaky $(flags) testsuite

disruptive: pipenv
	$(PYTEST) -mdisruptive --disruptive $(flags) testsuite

performance-smoke: pipenv
	$(PYTEST) --performance $(flags) testsuite/tests/performance/smoke

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
clean: mostlyclean
	rm -f Pipfile.lock

mostlyclean:
	rm -f .make-*
	-pipenv --rm

# Check http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
help: ## Print this help
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

release: ## Create branch of new VERSION (and tag VERSION)
release: VERSION-required Pipfile.lock
	$(RUNSCRIPT)make-next-release $(VERSION)
	git add VERSION
	git add -f Pipfile.lock
	git commit -m"`git rev-parse --abbrev-ref HEAD`"
	git tag -a "`git rev-parse --abbrev-ref HEAD|cut -c2-`" -m"`git rev-parse --abbrev-ref HEAD`"
	git rm --cached Pipfile.lock
	git commit -m"Unfreeze Pipfile.lock after release"

dist: ## Build (and push optionally) distribution-ready container image
dist: IMAGENAME ?= 3scale-py-testsuite
dist: pipenv
	git checkout `$(RUNSCRIPT)docker-tags -1`
	test -e VERSION
	$(RUNSCRIPT)docker-build $(IMAGENAME) `$(RUNSCRIPT)docker-tags`
	-[ -n "$$NOSWITCH" ] || git checkout -

VERSION-required:
ifndef VERSION
	$(error You must define VERSION=x.y.z)
endif

# this ensures dependent target is run everytime
FORCE:
