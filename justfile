# List available commands
default:
    @just --list

# Run tests with all extras
test *ARGS:
    uv run --all-extras pytest --no-cov {{ ARGS }}

# Run full test matrix (multiple Python versions + minimal deps)
test-matrix:
    #!/usr/bin/env bash
    set -uo pipefail
    rm -f .coverage .coverage.*
    FAILED=0
    for PY in 3.11 3.12 3.13; do
        echo ""
        echo "=== Python $PY ==="
        uv run --python $PY --all-extras coverage run -p -m pytest || FAILED=1
    done
    echo ""
    echo "=== Python 3.12 (minimal deps) ==="
    uv run --python 3.12 --with pytest --with pytest-cov --with coverage \
        coverage run -p -m pytest -m "not requires_api and not requires_serve and not requires_convert" || FAILED=1
    echo ""
    echo "=== Coverage Report ==="
    uv run --all-extras coverage combine
    uv run --all-extras coverage report
    uv run --all-extras coverage html
    echo "Coverage report saved to htmlcov/index.html"
    exit $FAILED

# Lint
lint:
    uv run --extra convert ruff check .

# Format code
fmt:
    uv run --extra convert ruff format .
    uv run --extra convert ruff check --fix .

# Check formatting without changing
check:
    uv run --extra convert ruff format --check .
    uv run --extra convert ruff check .

# Build docs
docs:
    cd docs && make html

# Live reload docs
docs-serve:
    cd docs && make nd

# Run an example
run example="counter":
    cd examples && uv run --all-extras python -m nanodjango run {{example}}.py
