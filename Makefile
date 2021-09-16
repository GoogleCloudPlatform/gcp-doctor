VERSION=$(shell sed -n 's/^current_version\s*=\s*//p' <.bumpversion.cfg)
DIST_NAME=gcp-doctor-$(VERSION)
SHELL=/bin/bash

test:
	pytest -o log_level=DEBUG --cov-config=.coveragerc --cov=gcp_doctor --forked

snapshots:
	pytest --snapshot-update

version:
	@echo $(VERSION)

build:
	rm -f dist/gcp-doctor
	pyinstaller --workpath=.pyinstaller.build pyinstaller.spec

bump-version:
	bumpversion --commit minor

tarfile:
	# TODO: replace with something based on setuptools?
	rm -rf dist-tmp
	mkdir -p dist-tmp/$(DIST_NAME)
	cp Pipfile Pipfile.lock README.md dist-tmp/$(DIST_NAME)
	cp gcp-doctor dist-tmp/$(DIST_NAME)
	chmod +x dist-tmp/$(DIST_NAME)/gcp-doctor
	cp --parents gcp_doctor/queries/client_secrets.json dist-tmp/$(DIST_NAME)
	find gcp_doctor -name '*.py' -exec cp --parents '{}' dist-tmp/$(DIST_NAME) ';'
	chmod -R a+rX dist-tmp
	mkdir -p dist
	tar -C dist-tmp -czf dist/gcp-doctor-$(VERSION).tar.gz --owner=0 --group=0 gcp-doctor-$(VERSION)
	rm -rf dist-tmp

release:
	# Make sure we are using the latest submitted code.
	git fetch
	git checkout origin/master
	# Remove '-test' in the version.
	# Note: this will fail if we have already a release tag, in which case
	# you should first increase the minor version with a code review.
	bumpversion --commit --tag --tag-message "Release v{new_version}" release
	# push to the release branch and tag the release
	git merge -s ours origin/release
	git push origin HEAD:release
	git push --tags
	# increment the version (and add back '-test')
	bumpversion --commit minor
	git push origin HEAD:refs/for/master

.PHONY: test coverage-report version build bump-version tarfile release
