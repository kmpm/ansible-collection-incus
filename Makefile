
.PHONY: clean
clean:
	@echo "Cleaning up..."
	@echo "Remove tests/output directories"
	rm -rf tests/output

	@echo "Remove all python related directories"
	find . -type d -name __pycache__ -exec rm -rf {} \;
	rm -rf .mypy_cache


.PHONY: test
test: test/sanity test/units


.PHONY: test/sanity
test/sanity:
	ansible-test sanity --python 3.11 -v


.PHONY: test/units
test/units:
	ansible-test units --venv --python 3.11
