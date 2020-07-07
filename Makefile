.PHONY: commit-acceptance pylint flake8 mypy all-is-package \
	test pytest tests smoke junit \
	pipenv pipenv-dev \
	container-image \
	clean

TB ?= short
LOGLEVEL ?= INFO

PYTEST = pipenv run python -m pytest --tb=$(TB) --log-level=$(LOGLEVEL)

commit-acceptance: pylint flake8 mypy all-is-package

pylint flake8 mypy: pipenv-dev
	pipenv run $@ $(flags) testsuite

all-is-package:
	@echo
	@echo "Searching for dirs missing __init__.py"
	@! find testsuite/ -type d \! -name __pycache__ \! -exec test -e {}/__init__.py \; -print | grep '^..*$$'

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
	$(PYTEST) --disruptive $(flags) testsuite

junit: pipenv
	$(PYTEST) --junitxml=junit.xml $(flags) testsuite

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

release: ## Push MR ready branch of new VERSION (and tag VERSION locally)
release: GITREMOTE ?= origin
release: VERSION-required Pipfile.lock
	echo $(VERSION)-r1 > VERSION
	git tag|grep -q $(VERSION)-r && git tag|grep $(VERSION)-r|sort -n -tr -k2|tail -1|sed -r 's/($(VERSION)-r)([0-9]+)/echo \1$$((\2+1))/e' > VERSION || :
	git checkout -b v`cat VERSION`
	git add VERSION
	git add -f Pipfile.lock
	git commit -m"v`cat VERSION`"
	git tag -a `cat VERSION` -m"v`cat VERSION`"
	git rm --cached Pipfile.lock
	git commit -m"Unfreeze Pipfile.lock after release"
	git push $(GITREMOTE) v`cat VERSION`
	-git checkout -

dist: ## Build (and push optionally) distribution-ready container image
dist: IMAGENAME ?= 3scale-py-testsuite
dist:
	test -e VERSION
	[ -n "$$NOSWITCH" ] || git checkout `cat VERSION`
	docker build -t $(IMAGENAME):`cat VERSION` .  # X.Y(.Z)-r#
	docker tag $(IMAGENAME):`cat VERSION` $(IMAGENAME):`cut -f1 -d- <VERSION`  # X.Y(.Z)
	grep -q '^[0-9]\+\.[0-9]\+\.[0-9]\+-r[0-9]\+' VERSION && \
		docker tag $(IMAGENAME):`cat VERSION` $(IMAGENAME):`cut -f1-2 -d. <VERSION` || :  # also X.Y of X.Y.Z
	# Don't tag/push latest for now, if 2.(n-1) gets tagged latest will be wrong
	# in theory this should not happen, but there is no check for this
	#grep -q '^[0-9]\+\.[0-9]\+-r[0-9]\+' VERSION && \
	#	docker tag $(IMAGENAME):`cat VERSION` $(IMAGENAME):latest || :  # if X.Y-r# (but not X.Y.Z-r#)
ifdef PUSHIMAGE
	docker push $(IMAGENAME):`cat VERSION`
	docker push $(IMAGENAME):`cut -f1 -d- <VERSION`
	grep -q '^[0-9]\+\.[0-9]\+\.[0-9]\+-r[0-9]\+' VERSION && \
		docker push $(IMAGENAME):`cut -f1-2 -d. <VERSION` || :
	#grep -q '^[0-9]\+\.[0-9]\+-r[0-9]\+' VERSION && \
	#	docker push $(IMAGENAME):latest || :
endif
	-[ -n "$$NOSWITCH" ] || git checkout -

VERSION-required:
ifndef VERSION
	$(error You must define VERSION=x.y.z)
endif
