.PHONY: commit-acceptance pylint flake8 mypy all-is-package \
	test pytest tests smoke junit \
	pipenv pipenv-dev \
	container-image \
	clean

TB ?= short
LOGLEVEL ?= INFO

# This is here for compatibility with osde2e workflow (reference?)
# It's a bit poisonous, firstly and most importantly NAMESPACE is too much
# generic variable name. Secondly this substitution is implemented here
# in Makefile and not in the testsuite.
ifdef NAMESPACE
_3SCALE_TESTS_OPENSHIFT__projects__threescale__name ?= $(NAMESPACE)
export _3SCALE_TESTS_OPENSHIFT__projects__threescale__name
endif

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
	$(PYTEST) $(flags) testsuite

debug: ## Run test  with debug flags
debug: flags := $(flags) -s
debug: test

smoke: pipenv
	$(PYTEST) -n6 -msmoke $(flags) testsuite

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

release: ## Submit MR of new VERSION
release: VERSION-required Pipfile.lock
	echo $(VERSION) > VERSION
	git checkout -b v$(VERSION)
	git add VERSION
	git add -f Pipfile.lock
	git commit -m"$(VERSION)"
	git tag -a $(VERSION) -m"$(VERSION)"
	git rm --cached Pipfile.lock
	git commit -m"Unfreeze Pipfile.lock after release"
	git push --tags origin v$(VERSION)
	git checkout -

dist: ## Build distribution-ready container image
dist: NAME ?= 3scale-py-testsuite
dist:
	test -e VERSION
	git checkout `cat VERSION`
	docker build -t $(NAME) .
	docker tag $(NAME) $(NAME):`cat VERSION`
	docker tag $(NAME) $(NAME):`cut -f1-2 -d. <VERSION`
	docker tag $(NAME) $(NAME):`cut -f1 -d. <VERSION`
	git checkout -

VERSION-required:
ifndef VERSION
	$(error You must define VERSION=x.y.z)
endif
