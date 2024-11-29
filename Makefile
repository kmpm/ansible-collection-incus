
usage:
	@echo "Usage: make [clean|test]"
	@echo "  clean: Remove all python related directories"
	@echo "  test: Run all tests"


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
	@echo "All tests passed"

.PHONY: test/sanity
test/sanity:
	@echo "Running sanity tests"
	ansible-test sanity --python 3.11 -v


.PHONY: test/units
test/units:
	@echo "Running unit tests"
	ansible-test units --venv --python 3.11
