.PHONY: test lint build
PYTHON ?= python3
QBUILD ?= qbuild

test:
	$(PYTHON) -m unittest discover -s tests -p 'test_*.py' -v

lint:
	# SC2015: the port-range guard intentionally fails if either bound is false.
	shellcheck --exclude=SC2015 -s sh shared/peach-qnap.sh
	sh -n package_routines
	sh -n qpkg.cfg

build:
	$(QBUILD) --root "$(CURDIR)" --build-arch x86_64 --build-dir "$(CURDIR)/dist" --gzip
