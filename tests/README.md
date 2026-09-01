# Automated testing of session4

## Running the automated tests

Run, from the top project directory:
> make test

This will result in a pytest report file ``PyTest_Report.html`` and a coverage report: ``index.html``
within an ``htmlcov/`` directory.

## Running the manual demo

To start the session4 Quixote demo that has been modified for testing
(in [../src/session4/modified_quix_demo](../src/session4/modified_quix_demo) )
either:--

* run, from the top project directory:
  > make altdemo

* OR move into the ``src/session4`` directory and run the demo.
  > uv run python -m quixote run --app modified_quix_demo.altdemo

Then vist <http://localhost:8080> in your browser.

## Quixote Demo

The standard Quxiote demo is also available, but does not currentlymake use of sessions.
Run from the ``src/session4`` directory:
> uv run python -m quixote run --app modified_quix_demo
