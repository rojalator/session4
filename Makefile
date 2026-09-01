# Makefile for Session4

# Sync .venv with the locked deps and an editable install (session4)
setup:
	uv sync

# Run from top-level directory. Creates a pytest html report and a coverage report (in htmlcov)
test:
	uv run pytest -s  --html PyTest_Report.html --cov=./ --cov-report html --log-cli-level=DEBUG

# Run the manual session-testing demo
altdemo:
	cd src/session4; uv run python -m quixote run --app modified_quix_demo.altdemo
