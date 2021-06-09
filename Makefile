all: .venv install test

.venv:
	virtualenv -p python3 .venv
	.venv/bin/pip install -r requirements.txt
	.venv/bin/pip install -r requirements-dev.txt

install:
	.venv/bin/python setup.py install

test:
	.venv/bin/py.test tests

clean:
	rm -Rf .venv 

.PHONY: install test
