.PHONY: test check

test:
	python3 -m unittest discover -s tests -v

check: test
	python3 sync/upstream-sync --help >/dev/null
	python3 cross/verify-toolchain --help >/dev/null
	bash cross/verify-ax23v-build --help >/dev/null
