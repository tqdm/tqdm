.PHONY: all flake8 test coverage

alltests: testcoverage flake8 testsetup
all: alltests build

flake8:
	flake8 --max-line-length=80 --count --statistics --exit-zero tqdm/
	flake8 --max-line-length=80 --count --statistics --exit-zero examples/

test:
	nosetests tqdm -v

testsetup:
	python setup.py check --restructuredtext --strict

testcoverage:
	nosetests tqdm --with-coverage --cover-package=tqdm -v

installdev:
	python setup.py develop --uninstall
	python setup.py develop

install:
	python setup.py install

build:
	python setup.py sdist --formats=gztar,zip bdist_wininst
	python setup.py sdist bdist_wheel

pypimeta:
	python setup.py register

pypi:
	twine upload dist/*
