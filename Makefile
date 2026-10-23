.PHONY: test lint build
PYTHON ?= python3
QBUILD ?= qbuild

test:
	$(PYTHON) -m unittest discover -s tests -p 'test_*.py' -v

lint:
	shellcheck -s sh shared/peach-qnap.sh
	sh -n package_routines
	sh -n qpkg.cfg

build:
	$(QBUILD) --root "$(CURDIR)" --build-arch x86_64 --build-dir "$(CURDIR)/dist" --gzip
