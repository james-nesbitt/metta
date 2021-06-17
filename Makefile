
.PHONY: lint
lint:
	for package in mirantis/testing/*; do \
	    if [ -d "$$package" ]; then echo "$$package"; pylint -d duplicate-code -d pointless-string-statement -d import-error $$package; fi; \
	done
	for package in suites/*/*; do \
	    if [ -d "$$package" ]; then echo "$$package"; pylint -d duplicate-code -d pointless-string-statement -d import-error $$package; fi; \
	done

.PHONY: clean
clean:
	rm -rf build dist *.log *.egg-info

build:
	python -m build

.PHONY: push
push:
	python -m -m twine upload dist/*
