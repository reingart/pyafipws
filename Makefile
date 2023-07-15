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

# Works with bash and linux
load-tests:
	cp conf/*.ini .
	curl -o reingart.zip https://www.sistemasagiles.com.ar/soft/pyafipws/reingart.zip
	python -m zipfile -e reingart.zip .

sign-tra:
	python -m pyafipws.wsaa

sign-cert:
	python -m pyafipws.wsfev1 --prueba

# Use "git clean -n" to see the files to be cleaned
# Use only when only the config files are untracked
# Finally use "git clean -f" to remove untracked files(in this case test files)

.PHONY: install test