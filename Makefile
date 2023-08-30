install:
	poetry install

format:
	poetry run autoflake --remove-all-unused-imports --recursive --remove-unused-variables --in-place simlib tests
	poetry run black simlib tests
	poetry run isort simlib tests

lint:
	poetry run mypy simlib tests
	poetry run flake8 simlib tests
	poetry run black simlib tests --check
	poetry run isort simlib tests --check-only
	poetry run pylint simlib tests
	poetry run bandit -r simlib

test: install
	poetry run pytest

clean:
	find . -name '*.pyc' -exec rm -rf {} +
	find . -name '*.egg-info' -exec rm -rf {} +
	find . -name '__pycache__' -exec rm -rf {} +
	rm -rf .mypy_cache
	rm -rf .pytest_cache
	rm -rf build/
	rm -rf dist/