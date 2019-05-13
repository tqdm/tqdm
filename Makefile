# IMPORTANT: for compatibility with `python setup.py make [alias]`, ensure:
# 1. Every alias is preceded by @[+]make (eg: @make alias)
# 2. A maximum of one @make alias or command per line
# see: https://github.com/tqdm/py-make/issues/1

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
	toxclean
	installdev
	install
	build
	buildupload
	pypi
	snap
	docker
	help
	none
	run

help:
	@python setup.py make -p

alltests:
	@+make testcoverage
	@+make testperf
	@+make flake8
	@+make testsetup

all:
	@+make alltests
	@+make build

flake8:
	@+flake8 --max-line-length=80 --exclude .asv,.tox,.ipynb_checkpoints,build \
    --ignore=W503,W504 -j 8 --count --statistics --exit-zero .

test:
	tox --skip-missing-interpreters

testnose:
	nosetests tqdm -d -v

testsetup:
	@make README.rst
	@make tqdm/tqdm.1
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

tqdm/tqdm.1: .tqdm.1.md tqdm/_main.py tqdm/_tqdm.py
	# TODO: add to mkdocs.py
	python -m tqdm --help | tail -n+5 |\
    sed -r -e 's/\\/\\\\/g' \
      -e 's/^  (--.*)=<(.*)>  : (.*)$$/\n\\\1=*\2*\n: \3./' \
      -e 's/  (-.*, )(--.*)  /\n\1\\\2\n: /' |\
    cat "$<" - |\
    pandoc -o "$@" -s -t man

README.rst: .readme.rst tqdm/_tqdm.py tqdm/_main.py
	@python mkdocs.py

snapcraft.yaml: .snapcraft.yml
	cat "$<" | sed -e 's/{version}/'"`python -m tqdm --version`"'/g' \
    -e 's/{commit}/'"`git describe --always`"'/g' \
    -e 's/{source}/./g' -e 's/{icon}/logo.png/g' \
    -e 's/{description}/https:\/\/tqdm.github.io/g' > "$@"

.dockerignore: .gitignore
	cat $^ > "$@"
	echo -e ".git" > "$@"
	git clean -xdn | sed -nr 's/^Would remove (.*)$$/\1/p' >> "$@"

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
submodules:
	git clone git@github.com:tqdm/tqdm.wiki wiki
	git clone git@github.com:tqdm/tqdm.github.io docs
	git clone git@github.com:conda-forge/tqdm-feedstock feedstock
	cd feedstock && git remote add autotick-bot git@github.com:regro-cf-autotick-bot/tqdm-feedstock

install:
	python setup.py install

build:
	@make prebuildclean
	@make testsetup
	python setup.py sdist bdist_wheel
	# python setup.py bdist_wininst

pypi:
	twine upload dist/*

buildupload:
	@make build
	@make pypi

snap:
	@make snapcraft.yaml
	snapcraft
docker:
	@make .dockerignore
	@make coverclean
	@make clean
	docker build . -t tqdm/tqdm
	docker tag tqdm/tqdm:latest tqdm/tqdm:$(shell docker run -i --rm tqdm/tqdm -v)
none:
	# used for unit testing

run:
	python -Om tqdm --help
