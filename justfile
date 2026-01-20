# List available commands
default:
    @just --list

# Run tests with all extras
test *ARGS:
    uv run --all-extras --group dev pytest --no-cov {{ ARGS }}

# Run full test matrix (multiple Python versions + minimal deps)
test-matrix:
    #!/usr/bin/env bash
    set -uo pipefail
    rm -f .coverage .coverage.* 2>/dev/null || true
    FAILED=0
    echo "Running test matrix:"
    for PY in 3.11 3.12 3.13; do
        printf "  Python $PY [all] ... "
        if uv run --python $PY --all-extras --group dev pytest -q --tb=no 2>&1 | tail -1; then
            true
        else
            FAILED=1
        fi
    done
    printf "  Python 3.12 [minimal] ... "
    if uv run --python 3.12 --group dev \
        pytest -q --tb=no -m "not requires_api and not requires_serve and not requires_convert" 2>&1 | tail -1; then
        true
    else
        FAILED=1
    fi
    echo ""
    echo "Running coverage (Python 3.12 [all])..."
    uv run --all-extras --group dev coverage run -m pytest -q --tb=no 2>&1 | grep -E "passed|failed" | tail -1
    uv run --all-extras --group dev coverage report
    uv run --all-extras --group dev coverage html
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
