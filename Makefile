UNAME_S := $(shell uname -s)
    ifeq ($(UNAME_S),Linux)
        SED = /bin/sed
    endif
    ifeq ($(UNAME_S),Darwin)
        SED = /usr/local/bin/gsed
    endif

PREV:=$(shell grep version= setup.py | $(SED) -E -e "s/\s*version='([0-9]*.[0-9]*)',/\1/")
NEXT:=$(shell echo $(PREV)+0.1 | /usr/bin/bc | $(SED) -E -e "s/^\./0\./")
DEPLOYURL=--repository-url https://test.pypi.org/legacy/
#DEPLOYURL=

all: clean build scs run

clean:
	rm -rf dist/* build/*

scs:
	mkdir -p scs

report: scs
	./pySCS.py models/sample

build: pySCS/pySCS.py
	cat setup.py | sed -e "s/'$(PREV)'/'$(NEXT)'/" > newver.py
	mv newver.py setup.py
	rm -rf dist/*
	python3 setup.py sdist bdist_wheel
	twine upload $(DEPLOYURL) dist/*

safety:
	safety check --file requirements-dev.txt

sast:
	bandit -r . --exclude=venv

lint:
	flake8 . --exclude=venv

autopep:
	autopep8 -r . --exclude venv --in-place

venv:
	virtualenv venv -p /usr/local/bin/python3.7
	pip install -r requirements-dev.txt

dist:
	python setup.py sdist bdist_wheel

upload-pypi-test:
	twine upload --repository-url https://test.pypi.org/legacy/ dist/*

venv-test:
	virtualenv test -p /usr/local/bin/python3.7
	pip install --index-url https://test.pypi.org/simple/ --no-deps py_scs


.PHONY: scs
