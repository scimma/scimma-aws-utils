.PHONY: lint
lint :
# stop the build if there are Python syntax errors or undefined names
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
# exit-zero treats all errors as warnings
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=100 --statistics

.PHONY: format
format :
	autopep8 --recursive --in-place .
	isort

.PHONY: pypi-dist
pypi-dist :
	python setup.py sdist bdist_wheel

.PHONY: pypi-dist-check
pypi-dist-check:
	twine check dist/*

.PHONY: pypi-upload
pypi-upload:
	twine upload dist/*

.PHONY: clean
clean:
	python setup.py clean
	rm -rf ./build/
	rm -rf ./dist/
