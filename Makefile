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

help:
	@python setup.py make

alltests:
	@+make testcoverage
	@+make testperf
	@+make flake8
	@+make testsetup

all:
	@+make alltests
	@+make build

flake8:
	@+flake8 --max-line-length=80 --exclude .asv,.tox -j 8 --count --statistics --exit-zero .

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

testperf:
	# do not use coverage (which is extremely slow)
	nosetests tqdm/tests/tests_perf.py -d -v

testtimer:
	nosetests tqdm --with-timer -d -v

# another performance test, to check evolution across commits
testasv:
	# Test only the last 3 commits (quick test)
	asv run -j 8 HEAD~3..HEAD
	@make viewasv

testasvfull:
	# Test all the commits since the beginning (full test)
	asv run -j 8 v1.0.0..master
	@make testasv

viewasv:
	asv publish
	asv preview

tqdm.1: tqdm.1.md
	python -m tqdm --help | tail -n+5 | cat "$<" - |\
    sed -r 's/^  (--.*)=<(.*)>  : (.*)$$/\n\\\1=*\2*\n: \3./' |\
    sed -r 's/  (-.*, --.*)  /\n\1\n: /' |\
    pandoc -o "$@" -s -t man

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
	@+python -c "import shutil; shutil.rmtree('tqdm/__pycache__', True)"
	@+python -c "import shutil; shutil.rmtree('tqdm/tests/__pycache__', True)"
clean:
	@+python -c "import os, glob; [os.remove(i) for i in glob.glob('*.py[co]')]"
	@+python -c "import os, glob; [os.remove(i) for i in glob.glob('tqdm/*.py[co]')]"
	@+python -c "import os, glob; [os.remove(i) for i in glob.glob('tqdm/tests/*.py[co]')]"
	@+python -c "import os, glob; [os.remove(i) for i in glob.glob('tqdm/examples/*.py[co]')]"
toxclean:
	@+python -c "import shutil; shutil.rmtree('.tox', True)"


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
