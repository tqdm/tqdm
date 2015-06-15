.PHONY: flake8 test coverage

flake8:
	flake8 --exclude "test_*" --max-line-length=80 --count --statistics --exit-zero tqdm/

test:
	nosetests tqdm -v

coverage:
	nosetests tqdm --with-coverage --cover-package=tqdm -v
