
.PHONY: lint
lint:
	for package in mirantis/testing/*; do \
	    if [ -d "$$package" ]; then echo "$$package"; pylint -d duplicate-code -d pointless-string-statement -d import-error $$package; fi; \
	done
	for package in suites/*; do \
	    if [ -d "$$package" ]; then echo "$$package"; pylint -d duplicate-code -d pointless-string-statement -d import-error $$package; fi; \
	done

.PHONY: pep8
pep8:
	autopep8 --recursive --aggressive --in-place --max-line-length=100 .
