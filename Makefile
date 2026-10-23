.PHONY: test lint build release
PYTHON ?= python3
QBUILD ?= qbuild

test:
	go test ./cmd/...
	$(PYTHON) -m unittest discover -s tests -p 'test_*.py' -v

lint:
	go vet ./cmd/...
	# SC2015: the port-range guard intentionally fails if either bound is false.
	shellcheck --exclude=SC2015 -s sh shared/peach-qnap.sh
	shellcheck -s sh shared/peach-admin-link.sh
	sh -n package_routines
	sh -n qpkg.cfg
	shellcheck -s bash scripts/build-release.sh

build: admin
	$(QBUILD) --root "$(CURDIR)" --build-arch x86_64 --build-dir "$(CURDIR)/dist" --gzip

# Requires a clean committed tree and Linux build dependencies.
release:
	bash scripts/build-release.sh "$(TAG)"

.PHONY: admin
admin:
	CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -trimpath -ldflags="-s -w" -o shared/peach-admin.cgi ./cmd/peach-admin
