.PHONY: commit-acceptance pylint flake8 mypy all-is-package \
	test pytest tests smoke junit \
	pipenv pipenv-dev \
	container-image \
	clean

TB ?= short
LOGLEVEL ?= INFO

ifdef WORKSPACE  # Yes, this is for jenkins
resultsdir = $(WORKSPACE)
else
resultsdir ?= .
endif

PIPENV_VERBOSITY ?= -1
PIPENV_IGNORE_VIRTUALENVS ?= 1

ifdef junit
flags += --junitxml=$(resultsdir)/junit-$@.xml -o junit_suite_name=$@
endif

persistence_file ?= $(resultsdir)/pytest-persistence.pickle

PYTEST = pipenv run python -m pytest --tb=$(TB)
RUNSCRIPT = pipenv run ./scripts/

ifeq ($(filter $(--store||--load),$(flags)),$(flags))
	PYTEST += -p no:persistence
endif

commit-acceptance: pylint flake8 mypy all-is-package

pylint flake8 mypy: pipenv-dev
	pipenv run $@ $(flags) testsuite

all-is-package:
	@echo
	@echo "Searching for dirs missing __init__.py"
	@! find testsuite/ -type d \! -name __pycache__ \! -path 'testsuite/resources/*' \! -exec test -e {}/__init__.py \; -print | grep '^..*$$'

# pattern to run individual testfile or all testfiles in directory
testsuite/%: FORCE pipenv
	$(PYTEST) -v --performance --ui --disruptive --toolbox $(flags) $@

test: ## Run test
test pytest tests: pipenv
	$(PYTEST) -n4 -m 'not flaky' --dist loadfile $(flags) testsuite

speedrun: ## Bigger than smoke faster than test
speedrun: pipenv
	$(PYTEST) -n4 -m 'not flaky' --drop-sandbag $(flags) testsuite

persistence: ## Run speedrun tests compatible with persistence plugin. Use persitence-store|persistence-load instead
persistence: pipenv
	$(PYTEST) -n4 -m 'not flaky' --drop-sandbag --drop-nopersistence $(flags) testsuite

persistence-store persistence-load: export _3SCALE_TESTS_skip_cleanup=true
persistence-store persistence-load: pipenv
	$(subst -p no:persistence,,$(PYTEST)) -n4 -m 'not flaky' --drop-sandbag --drop-nopersistence $(flags) --$(subst persistence-,,$@) $(persistence_file) testsuite

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

toolbox: pipenv
	$(PYTEST) --toolbox $(flags) testsuite/tests/toolbox

test-in-docker: ## Run test in container with selenium sidecar
test-in-docker: rand := $(shell echo $$RANDOM)  # bashism!!!
test-in-docker: network := test3scale_$(rand)
test-in-docker: selenium_name := selenium_$(rand)
test-in-docker: image ?= quay.io/rh_integration/3scale-testsuite
test-in-docker: selenium_image ?= selenium/standalone-chrome
test-in-docker: KUBECONFIG ?= $(HOME)/.kube/config
test-in-docker: SECRETS_FOR_DYNACONF ?= $(if $(wildcard ./config/.secrets.yaml),./config/.secrets.yaml,./config/settings.local.yaml)
test-in-docker:
	docker network create $(network)
	docker run -d --name $(selenium_name) --network $(network) --network-alias selenium -v /dev/shm:/dev/shm $(selenium_image)
	-docker run \
		--network $(network) \
		-v `readlink -f $(SECRETS_FOR_DYNACONF)`:/opt/secrets.yaml:z \
		-v `readlink -f $(KUBECONFIG)`:/opt/kubeconfig:z \
		-v `readlink -f $(resultsdir)`:/test-run-results:z \
		-e NAMESPACE \
		`env | grep _3SCALE_TESTS_ | sed 's/^/-e /'` \
		-e _3SCALE_TESTS_fixtures__ui__browser__source=remote \
		-e _3SCALE_TESTS_fixtures__ui__browser__remote_url=http://selenium:4444 \
		$(docker_flags) \
		$(image) $(cmd)
	docker rm -f $(selenium_name)
	docker network rm $(network)

# Weird behavior of make (bug?), target specific variables don't seem to be
# exported elsewhere. These lines have to be below related target
ifdef KUBECONFIG
export KUBECONFIG
endif
ifdef SECRETS_FOR_DYNACONF
export SECRETS_FOR_DYNACONF
endif

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
container-image: IMAGENAME ?= 3scale-tests
container-image: fetch-tools
	$(RUNSCRIPT)docker-build $(IMAGENAME) latest

clean: ## clean pip deps
clean: mostlyclean
	rm -f Pipfile.lock

mostlyclean:
	rm -f .make-*
	rm -rf .mypy_cache
	-pipenv --rm

all: ## Run all the tests and submit results to reportportal (may require -k)
all: .ensure-smoke ensure-smoke test disruptive flaky reportportal

# Check http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
help: ## Print this help
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

polish-junit: ## Remove skipped tests and logs from passing tests
polish-junit:
	gzip -f $(resultsdir)/junit-*.xml
	# 'cat' on next line is neessary to avoid wipe of the files
	for file in $(resultsdir)/junit-*.xml.gz; do zcat $$file | xsltproc ./xslt/polish-junit.xsl - >$${file%.gz}; done  # bashism!!!
	# this deletes something it didn't create, dangerous!!!
	-rm -f $(resultsdir)/junit-*.xml.gz

reportportal: RP_PROJECT ?= 3scale
reportportal: RP_LAUNCH_NAME ?= ad-hoc with tests $(shell cat VERSION)
reportportal: polish-junit
	$(RUNSCRIPT)junit2reportportal \
		--reportportal $(REPORTPORTAL) \
		--project $(RP_PROJECT) --launch-name "$(RP_LAUNCH_NAME)" \
		--token-variable RP_TOKEN \
		$(resultsdir)/junit-*.xml

testsuite/resources/apicast.yml: export VERSION ?= $(shell cut -d. -f1-3 VERSION)
testsuite/resources/apicast.yml: FORCE
	$(RUNSCRIPT)env-version-check
	curl -f https://raw.githubusercontent.com/3scale/3scale-amp-openshift-templates/$(VERSION).GA/apicast-gateway/apicast.yml > $@ || \
	curl -f https://raw.githubusercontent.com/3scale/3scale-amp-openshift-templates/master/apicast-gateway/apicast.yml > $@
	sed -i "s/imagePullPolicy:.*/imagePullPolicy: Always/g" $@

release: ## Create branch of new VERSION (optionally tag VERSION)
release: tag_release ?= no
ifeq ($(VERSION),)
release: export VERSION := $(shell cut -d. -f1-3 VERSION)
endif
release: Pipfile.lock testsuite/resources/apicast.yml pipenv-dev
	$(RUNSCRIPT)env-version-check
	$(RUNSCRIPT)make-next-release $(VERSION)
	git add testsuite/VERSION
	git add -f Pipfile.lock
	git add testsuite/resources/apicast.yml
	git commit -m"`git rev-parse --abbrev-ref HEAD`"
	echo "$$tag_release" | egrep -iq '^(false|no|f|n|0)$$' || git tag -a "`git rev-parse --abbrev-ref HEAD|sed 's/^3scale-tests-//'`" -m"`git rev-parse --abbrev-ref HEAD`"
	git rm --cached Pipfile.lock
	git commit -m"Unfreeze Pipfile.lock after release"

dist: ## Build (and push optionally) distribution-ready container image
dist: IMAGENAME ?= 3scale-testsuite
dist: pipenv fetch-tools
	git checkout v`$(RUNSCRIPT)docker-tags -1`
	test -e VERSION
	$(RUNSCRIPT)docker-build $(IMAGENAME) `$(RUNSCRIPT)docker-tags`
	-[ -n "$$NOSWITCH" ] || git checkout -

fetch-tools:
	-rm -Rf ext/testsuite-tools/
	-mkdir -p ext/
	-curl $(fetch_tools) | tar -C ext/ -xz

tools:
	SHARED_NAMESPACE=tools ./ext/testsuite-tools/run.sh

VERSION-required:
ifndef VERSION
	$(error You must define VERSION=x.y.z)
endif

.ensure-smoke: smoke
	@touch $@

ensure-smoke:
	$(if $(wildcard .$@),,$(error smoke failed))
	@rm -f .$@

fake-sync:
	test -e Pipfile.lock \
		&& touch Pipfile.lock \
		&& touch .make-pipenv-sync .make-pipenv-sync-dev \
		|| true

# this ensures dependent target is run everytime
FORCE:
