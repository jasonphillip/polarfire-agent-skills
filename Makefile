.PHONY: env test
PYTHON311 := $(shell command -v python3.11)
env:
	@test -n "$(PYTHON311)" || { echo 'python3.11 is required'; exit 1; }
	$(PYTHON311) -m venv .venv
	.venv/bin/python -m pip install --extra-index-url https://download.pytorch.org/whl/cpu -e '.[test,odmr]'
	.venv/bin/python -m pfkit deps fetch
	.venv/bin/python -m pip freeze > .venv/freeze.txt
	touch .venv/.ready

test:
	.venv/bin/python -m pytest -q
