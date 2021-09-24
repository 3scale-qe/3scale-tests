.PHONY: commit-acceptance pylint flake8 mypy all-is-package \
	test pytest tests smoke junit \
	pipenv pipenv-dev \
	container-image \
	clean

TB ?= short
LOGLEVEL ?= INFO
resultsdir ?= .

ifdef junit
flags += --junitxml=$(resultsdir)/junit-$@.xml -o junit_suite_name=$@
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
	$(PYTEST) --performance --ui --disruptive --toolbox $(flags) $@

test: ## Run test
test pytest tests: pipenv
	$(PYTEST) -n4 -m 'not flaky' $(flags) testsuite

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

ui: pipenv
	$(PYTEST) --ui $(flags) testsuite/tests/ui

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
container-image: fetch-tools
	docker build -t 3scale-py-testsuite .

clean: ## clean pip deps
clean: mostlyclean
	rm -f Pipfile.lock

mostlyclean:
	rm -f .make-*
	-pipenv --rm

all: ## Run all the tests and submit results to reportportal (may require -k)
all: .ensure-smoke ensure-smoke test disruptive flaky reportportal

# Check http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
help: ## Print this help
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

reportportal: RP_PROJECT ?= 3scale
reportportal: RP_LAUNCH_NAME ?= ad-hoc with tests $(shell cat VERSION)
reportportal:
	$(RUNSCRIPT)junit2reportportal \
		--reportportal $(REPORTPORTAL) \
		--project $(RP_PROJECT) --launch-name "$(RP_LAUNCH_NAME)" \
		--token-variable RP_TOKEN \
		$(resultsdir)/junit-*.xml

testsuite/resources/apicast.yml: FORCE VERSION-required
	curl -f https://raw.githubusercontent.com/3scale/3scale-amp-openshift-templates/$(VERSION).GA/apicast-gateway/apicast.yml > $@ || \
	curl -f https://raw.githubusercontent.com/3scale/3scale-amp-openshift-templates/master/apicast-gateway/apicast.yml > $@
	sed -i "s/imagePullPolicy:.*/imagePullPolicy: Always/g" $@

release: ## Create branch of new VERSION (and tag VERSION)
release: VERSION-required Pipfile.lock testsuite/resources/apicast.yml
	$(RUNSCRIPT)make-next-release $(VERSION)
	git add testsuite/VERSION
	git add -f Pipfile.lock
	git add testsuite/resources/apicast.yml
	git commit -m"`git rev-parse --abbrev-ref HEAD`"
	git tag -a "`git rev-parse --abbrev-ref HEAD|cut -c2-`" -m"`git rev-parse --abbrev-ref HEAD`"
	git rm --cached Pipfile.lock
	git commit -m"Unfreeze Pipfile.lock after release"

dist: ## Build (and push optionally) distribution-ready container image
dist: IMAGENAME ?= 3scale-py-testsuite
dist: pipenv fetch-tools
	git checkout `$(RUNSCRIPT)docker-tags -1`
	test -e VERSION
	$(RUNSCRIPT)docker-build $(IMAGENAME) `$(RUNSCRIPT)docker-tags`
	-[ -n "$$NOSWITCH" ] || git checkout -

fetch-tools:
	-rm -Rf testsuite-tools/
	-curl $(fetch_tools) | tar -xz

tools:
	./testsuite-tools/run.sh

VERSION-required:
ifndef VERSION
	$(error You must define VERSION=x.y.z)
endif

.ensure-smoke: smoke
	@touch $@

ensure-smoke:
	$(if $(wildcard .$@),,$(error smoke failed))
	@rm -f .$@

# this ensures dependent target is run everytime
FORCE:
