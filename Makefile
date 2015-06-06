.PHONY: test flake8 coverage clean

help:
	@echo "Please use make <target> where <target> is one of"
	@echo "    test                 : run tests"
	@echo "    flake8               : run flake8 to check PEP8"
	@echo "    coverage             : run tests and check code coverage"
	@echo "    clean                : clean current repository"

test:
	nosetests tqdm/ -v

flake8:
	flake8 --exclude "test_*" --max-line-length=100 --count --statistics --exit-zero tqdm/

coverage:
	nosetests --with-coverage --cover-package=tqdm -v tqdm/

clean:
	find . -name "*.so" -exec rm -rf {} \;
	find . -name "*.pyc" -exec rm -rf {} \;
	find . -depth -name "__pycache__" -type d -exec rm -rf '{}' \;
	rm -rf build/ dist/ tqdm.egg-info/
