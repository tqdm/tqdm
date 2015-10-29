.PHONY: all flake8 test coverage

all: flake8 coverage
flake8:
	flake8 --max-line-length=80 --count --statistics --exit-zero tqdm/
	flake8 --max-line-length=80 --count --statistics --exit-zero examples/

test:
	nosetests tqdm -v

coverage:
	rm -f .coverage  # coverage erase
	nosetests tqdm --with-coverage --cover-package=tqdm -v
