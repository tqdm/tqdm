# IMPORTANT: for compatibility with `python setup.py make [alias]`, ensure:
# 1. Every alias is preceded by @[+]make (eg: @make alias)
# 2. A maximum of one @make alias or command per line
#
# Sample makefile compatible with `python setup.py make`:
#```
#all:
#	@make test
#	@make install
#test:
#	nosetest
#install:
#	python setup.py install
#```

.PHONY:
	alltests
	all
	flake8
	test
	testnose
	testsetup
	testcoverage
	testperf
	testtimer
	distclean
	coverclean
	prebuildclean
	clean
	installdev
	install
	build
	pypimeta
	pypi
	none

alltests:
	@+make testcoverage
	@+make testperf
	@+make flake8
	@+make testsetup

all:
	@+make alltests
	@+make build

flake8:
	@+flake8 --max-line-length=80 --count --statistics --exit-zero tqdm/
	@+flake8 --max-line-length=80 --count --statistics --exit-zero examples/
	@+flake8 --max-line-length=80 --count --statistics --exit-zero .
	@+flake8 --max-line-length=80 --count --statistics --exit-zero tqdm/tests/

test:
	tox --skip-missing-interpreters

testnose:
	nosetests tqdm -d -v

testsetup:
	python setup.py check --restructuredtext --strict
	python setup.py make none

testcoverage:
	@make coverclean
	nosetests tqdm --with-coverage --cover-package=tqdm --cover-erase --cover-min-percentage=80 --ignore-files="tests_perf\.py" -d -v

testperf:  # do not use coverage (which is extremely slow)
	nosetests tqdm/tests/tests_perf.py -d -v

testtimer:
	nosetests tqdm --with-timer -d -v

distclean:
	@+make coverclean
	@+make prebuildclean
	@+make clean
prebuildclean:
	@+python -c "import shutil; shutil.rmtree('build', True)"
	@+python -c "import shutil; shutil.rmtree('dist', True)"
	@+python -c "import shutil; shutil.rmtree('tqdm.egg-info', True)"
coverclean:
	@+python -c "import os; os.remove('.coverage') if os.path.exists('.coverage') else None"
clean:
	@+python -c "import os; import glob; [os.remove(i) for i in glob.glob('*.py[co]')]"
	@+python -c "import os; import glob; [os.remove(i) for i in glob.glob('tqdm/*.py[co]')]"
	@+python -c "import os; import glob; [os.remove(i) for i in glob.glob('tqdm/tests/*.py[co]')]"

installdev:
	python setup.py develop --uninstall
	python setup.py develop

install:
	python setup.py install

build:
	@make prebuildclean
	python setup.py sdist --formats=gztar,zip bdist_wheel
	python setup.py bdist_wininst

pypimeta:
	python setup.py register

pypi:
	twine upload dist/*

buildupload:
	@make testsetup
	@make build
	@make pypimeta
	@make pypi

none:
	# used for unit testing
