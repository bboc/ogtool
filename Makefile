init:
	pip install -r requirements.txt

test:
	nosetests

dev:
	python setup.py develop
