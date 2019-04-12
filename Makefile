UNAME_S := $(shell uname -s)
    ifeq ($(UNAME_S),Linux)
        SED = /usr/bin/sed
    endif
    ifeq ($(UNAME_S),Darwin)
        SED = /usr/local/bin/gsed
    endif

PREV:=$(shell grep version= setup.py | $(SED) -E -e "s/\s*version='([0-9]*.[0-9]*)',/\1/")
NEXT:=$(shell echo $(PREV)+0.1 | /usr/bin/bc | $(SED) -E -e "s/^\./0\./")
DEPLOYURL=--repository-url https://test.pypi.org/legacy/
#DEPLOYURL=

all: clean build scs report

clean:
	rm -rf dist/* build/*

scs:
	mkdir -p scs

dfd:
	./pySCS.py --dfd | dot -Tpng -o dfd.png

seq:
	./pySCS.py --seq | java -Djava.awt.headless=true -jar ./plantuml.jar -tpng -pipe > seq.png

report: scs dfd seq
	./pySCS.py --report templates/template_sample.md > scs/report.md

build: pytm/pytm.py
	cat setup.py | sed -e "s/'$(PREV)'/'$(NEXT)'/" > newver.py
	mv newver.py setup.py
	rm -rf dist/*
	python3 setup.py sdist bdist_wheel
	twine upload $(DEPLOYURL) dist/*

.PHONY: scs
