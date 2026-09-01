# Makefile for Session4

# Handy macros
PDOC = pydoctor --make-html --docformat="plaintext" --disable-intersphinx-cache --project-name "Session4" --html-output
# PYCCO needs re-writing!
# PYCCO := pycco --generate_index --paths --skip-bad-files  --directory

# Sync .venv with the locked deps and an editable install (session4)
setup:
	uv sync

# Run from top-level directory. Creates a pytest html report and a coverage report (in htmlcov)
test:
	uv run pytest -s  --html PyTest_Report.html --cov=./ --cov-report html --log-cli-level=DEBUG

# Run the manual session-testing demo
altdemo:
	cd src/session4; uv run python -m quixote run --app modified_quix_demo.altdemo

documentation:
	uv run $(PDOC) doc/api src/session4
	# uv run $(PYCCO) doc/literate src/session4/*.py src/session4/*.py tests/*.py

# Call 'make clean' to get rid of the documentation directory's html entries
# No directory or file will be called 'clean' so mark it as a phony
.PHONY: clean
clean:
	rm -rf doc/api/*
	rm -rf doc/literate/*
	rm -rf dist/*

build:	clean
	uv build --clear
