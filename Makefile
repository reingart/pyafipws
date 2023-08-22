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
# This command first copies all the configuration settings from the conf folder
# to the main folder and next it downloads test key and digital certificate that 
# that can be used for testing and lastly the python module is used to decompress
# the files
get-auth:
	cp conf/*.ini .
	curl -o reingart.zip https://www.sistemasagiles.com.ar/soft/pyafipws/reingart.zip
	python -m zipfile -e reingart.zip .

access-ticket:
	python -m pyafipws.wsaa

sample-invoice:
	python -m pyafipws.wsfev1 --prueba

# Use "git clean -n" to see the files to be cleaned
# Use only when only the config files are untracked
# Finally use "git clean -f" to remove untracked files(in this case test files)
# This command will list all the files that are untracked. You can clean them verbosely
# using git clean -i. Else, if you are sure, you can se -f to remove all untracked files
# without a prompt
clean-test:
	git clean -n
	git clean -i

.PHONY: install test get-auth sample-invoice sign-cert
