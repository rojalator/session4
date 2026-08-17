

# Sync .venv with the locked deps and an editable install (session4)
setup:
	uv sync

# Run from top-level directory. Creates a pytest html report and a coverage report (in htmlcov)
test:
	pytest --html PyTest_Report.html --cov=./ --cov-report html
