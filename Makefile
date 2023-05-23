.PHONY: commit-acceptance pylint flake8 mypy all-is-package black-check \
	test pytest tests smoke junit \
	pipenv pipenv-dev \
	container-image \
	clean

SHELL = /bin/bash

TB ?= short
LOGLEVEL ?= INFO

ifdef WORKSPACE  # Yes, this is for jenkins
resultsdir = $(WORKSPACE)
else
resultsdir ?= .
endif

export resultsdir

PIPENV_VERBOSITY ?= -1
PIPENV_IGNORE_VIRTUALENVS ?= 1

persistence_file ?= $(resultsdir)/pytest-persistence.pickle

PYTEST = pipenv run python -m pytest --tb=$(TB) -o cache_dir=$(resultsdir)/.pytest_cache.$(@F)
RUNSCRIPT = pipenv run ./scripts/

ifdef junit
PYTEST += --junitxml=$(resultsdir)/junit-$(@F).xml -o junit_suite_name=$(@F)
endif

ifdef html
PYTEST += --html=$(resultsdir)/report-$(@F).html --self-contained-html
endif

ifdef PYTHON_VERSION
PIPENV_ARGS += --python $(PYTHON_VERSION)
endif

ifeq ($(filter-out --store --load,$(flags)),$(flags))
	PYTEST += -p no:persistence
endif

commit-acceptance: pylint flake8 mypy all-is-package black-check

pylint flake8 mypy: pipenv-dev
	pipenv run $@ $(flags) testsuite

black-check: pipenv-dev
	pipenv run black --check testsuite

all-is-package:
	@echo
	@echo "Searching for dirs missing __init__.py"
	@! find testsuite/ -type d \! -name __pycache__ \! -path 'testsuite/resources/*' \! -exec test -e {}/__init__.py \; -print | grep '^..*$$'

.PRECIOUS: testsuite/%
# pattern to run individual testfile or all testfiles in directory
testsuite/%: FORCE pipenv check-secrets.yaml
	$(PYTEST) -v --performance --ui --disruptive --toolbox $(flags) $@

test: ## Run test
test pytest tests: pipenv check-secrets.yaml
	$(PYTEST) -n4 --dist loadfile -m 'not flaky' $(flags) testsuite

speedrun: ## Bigger than smoke faster than test
speedrun: pipenv check-secrets.yaml
	$(PYTEST) -n4 --dist loadfile -m 'not flaky' --drop-sandbag $(flags) testsuite

capabilities-speedrun: pipenv check-secrets.yaml
	$(PYTEST) -n1 -m 'not flaky' --drop-sandbag --capabilities $(flags) testsuite

sandbag:  ## Complemetary set to speedrun that makes the rest of test target (speedrun+sandbag == test)
sandbag: pipenv
	$(PYTEST) -n4 --dist loadfile -m 'not flaky' --sandbag $(flags) testsuite

persistence: ## Run speedrun tests compatible with persistence plugin. Use persitence-store|persistence-load instead
persistence: pipenv check-secrets.yaml
	$(PYTEST) -n4 --dist loadfile -m 'not flaky' --drop-nopersistence $(flags) testsuite

persistence-store persistence-load: export _3SCALE_TESTS_skip_cleanup=true
persistence-store persistence-load: pipenv check-secrets.yaml
	$(subst -p no:persistence,,$(PYTEST)) -n4 --dist loadfile -m 'not flaky' --drop-nopersistence $(flags) --$(subst persistence-,,$@) $(persistence_file) testsuite

debug: ## Run test  with debug flags
debug: flags := $(flags) -s
debug: test

smoke: pipenv check-secrets.yaml
	$(PYTEST) -n6 -msmoke $(flags) testsuite

capabilities-smoke: pipenv check-secrets.yaml
	$(PYTEST) -n3 -msmoke --capabilities $(flags) testsuite

flaky: pipenv check-secrets.yaml
	$(PYTEST) -mflaky $(flags) testsuite

disruptive: pipenv check-secrets.yaml
	$(PYTEST) -mdisruptive --disruptive $(flags) testsuite

performance-smoke: pipenv check-secrets.yaml
	$(PYTEST) --performance $(flags) testsuite/tests/performance/smoke

ui: pipenv check-secrets.yaml
	$(PYTEST) --ui $(flags) testsuite/tests/ui

toolbox: pipenv check-secrets.yaml
	$(PYTEST) --toolbox $(flags) testsuite/tests/toolbox

test-images:
	$(PYTEST) --images $(flags) testsuite/tests/images

test-in-docker: ## Run test in container with selenium sidecar
test-in-docker: rand := $(shell cut -d- -f1 /proc/sys/kernel/random/uuid)
test-in-docker: network := test3scale_$(rand)
test-in-docker: selenium_name := selenium_$(rand)
test-in-docker: image ?= ghcr.io/3scale-qe/3scale-tests
test-in-docker: selenium_image ?= selenium/standalone-chrome
test-in-docker: KUBECONFIG ?= $(HOME)/.kube/config
test-in-docker: DOCKERCONFIGJSON ?= $(HOME)/.docker/config.json
ifdef use_dockerconfig
test-in-docker: _dockerconfigjson = -v `readlink -f $(DOCKERCONFIGJSON)`:/run/dockerconfig.json:z -e DOCKERCONFIGJSON=/run/dockerconfig.json
endif
ifeq ($(shell docker --version 2>/dev/null|grep -o podman), podman)
test-in-docker: _docker_flags = --userns=keep-id
endif
ifdef SECRETS_FOR_DYNACONF
test-in-docker: _secrets_for_dynaconf = -v `readlink -f $(SECRETS_FOR_DYNACONF)`:/opt/secrets.yaml:z
endif
test-in-docker:
test-in-docker: check-secrets.yaml
ifdef pull
	docker pull $(image)
endif
	docker network create $(network)
	docker run -d --name $(selenium_name) --network $(network) --network-alias selenium -v /dev/shm:/dev/shm $(selenium_image)
	-docker run \
		-it \
		--rm \
		--network $(network) \
		$(_secrets_for_dynaconf) \
		-v `readlink -f ./config`:/opt/workdir/3scale-py-testsuite/config:z \
		-v `readlink -f $(KUBECONFIG)`:/opt/kubeconfig:z \
		-v `readlink -f $(resultsdir)`:/test-run-results:z \
		$(_dockerconfigjson) \
		-e ENV_FOR_DYNACONF \
		-e NAMESPACE \
		`env | awk -F= '/^_3SCALE_TESTS_/{print "-e", $$1}'` \
		-e flags \
		-e _3SCALE_TESTS_fixtures__ui__browser__source=remote \
		-e _3SCALE_TESTS_fixtures__ui__browser__remote_url=http://selenium:4444 \
		-u $(shell id -u) \
		$(_docker_flags) \
		$(docker_flags) \
		$(image) $(cmd)
	docker rm -f $(selenium_name)
	docker network rm $(network)

# Weird behavior of make (bug?), target specific variables don't seem to be
# exported elsewhere. These lines have to be below related target
ifdef KUBECONFIG
export KUBECONFIG
endif
ifdef DOCKERCONFIGJSON
export DOCKERCONFIGJSON
endif

Pipfile.lock: Pipfile
	pipenv lock $(PIPENV_ARGS)

.make-pipenv-sync: Pipfile.lock
	pipenv sync $(PIPENV_ARGS)
	touch .make-pipenv-sync

.make-pipenv-sync-dev: Pipfile.lock
	pipenv sync --dev $(PIPENV_ARGS)
	touch .make-pipenv-sync-dev .make-pipenv-sync

pipenv: .make-pipenv-sync

pipenv-dev: .make-pipenv-sync-dev

container-image: ## Build container image
container-image: IMAGENAME ?= 3scale-tests
container-image: fetch-tools
ifdef CACERT
	docker build -t $(IMAGENAME) --build-arg=$(CACERT) .
else
	docker build -t $(IMAGENAME) .
endif

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
	for file in $(resultsdir)/junit-*.xml.gz; do zcat $$file | $(RUNSCRIPT)xslt-apply ./xslt/polish-junit.xsl >$${file%.gz}; done  # bashism!!!
	# this deletes something it didn't create, dangerous!!!
	-rm -f $(resultsdir)/junit-*.xml.gz

reportportal: ## Upload results to reportportal. Appropriate variables for juni2reportportal must be set
reportportal: polish-junit
	$(RUNSCRIPT)junit2reportportal $(resultsdir)/junit-*.xml

polarion: ## Upload results to polarion. Appropriate variables for juni2polarion must be set
polarion: polish-junit
	$(RUNSCRIPT)junit2polarion $(resultsdir)/junit-*.xml

testsuite/resources/apicast.yml: export VERSION ?= $(shell cut -d. -f1-3 VERSION)
testsuite/resources/apicast.yml: FORCE
	$(RUNSCRIPT)env-version-check
	curl -f https://raw.githubusercontent.com/3scale/3scale-amp-openshift-templates/$(VERSION).GA/apicast-gateway/apicast.yml > $@ || \
	curl -f https://raw.githubusercontent.com/3scale/3scale-amp-openshift-templates/master/apicast-gateway/apicast.yml > $@
	sed -i -e "s/imagePullPolicy:.*/imagePullPolicy: Always/g" \
	       -e "/^apiVersion:/s^:.*^: template.openshift.io/v1^" $@

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
dist: _version = $(shell git describe --tags --abbrev=0)
dist: pipenv fetch-tools
	git checkout $(_version)
	test -e VERSION
ifdef CACERT
	docker build `$(RUNSCRIPT)semver-docker-tags "-t $(IMAGENAME)" $(_version) 4` --build-arg "cacert=$(CACERT)" .
else
	docker build `$(RUNSCRIPT)semver-docker-tags "-t $(IMAGENAME)" $(_version) 4` .
endif
ifdef PUSHIMAGE
	$(RUNSCRIPT)semver-docker-tags $(IMAGENAME) $(_version) 4|tr ' ' '\n'|xargs -l docker push
ifdef PUSH_EXTRA
	$(RUNSCRIPT)semver-docker-tags $(IMAGENAME) $(_version) 4|tr ' ' '\n'|head -1|xargs -I{} docker tag {} $(PUSH_EXTRA)
	docker push $(PUSH_EXTRA)
endif
endif
	-[ -n "$$NOSWITCH" ] || git checkout -

fetch-tools: _targetdir=ext/testsuite-tools
fetch-tools:
	-rm -Rf $(_targetdir)
	-mkdir -p $(_targetdir)
	-curl -L $(fetch_tools) | tar --strip-components=1 -C $(_targetdir) -xz

# For now deploy all tools to same namespace, it is safe unless more deployment
# methods are used. Different deployment method of tools should be used for such cases.
tools: export THREESCALE_NAMESPACE ?= tools
tools: export SHARED_NAMESPACE ?= tools
tools:
	./ext/testsuite-tools/run.sh

define n


endef
check-secrets.yaml:
ifeq ($(shell grep -lIL . config/.secrets.yaml), config/.secrets.yaml)
	$(error config/.secrets.yaml contains binary data! See README.md$nEither (if you can):$n $$ git crypt unlock$nor delete it:$n $$ rm config/.secrets.yaml$n)
endif


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
