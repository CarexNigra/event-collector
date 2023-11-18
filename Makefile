.ONESHELL:
SHELL := /bin/bash

.SILENT:

%:
	@:

DEFAULT_GOAL := help
.PHONY: help
help:
	awk 'BEGIN {FS = ":.*?## "} /^[%a-zA-Z_-]+:.*?## / {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

.PHONY: install
install: ## Create poetry environment and install all dependencies
	poetry config virtualenvs.in-project true --local
	poetry env use 3.11
	poetry install
	poetry run pre-commit install --allow-missing-config

.PHONY: style-check
style-check: ## Run style checks.
	printf "Style Checking with Flake8, Black and Isort\n"
	poetry run black --config pyproject.toml --check .
	poetry run flake8 --max-line-length=120 --ignore="E402,W291,E203" --exclude="*__init__.py" .
	poetry run isort --check-only --diff .

.PHONY: static-check
static-check: ## Run strict typing checks.
	printf "Static Checking with Mypy\n"
	poetry run mypy library service --config-file pyproject.toml --exclude '(**/*/tests/*)'

.PHONY: black
black: ## Run black on local machine.
	poetry run black --config pyproject.toml .

.PHONY: isort
isort: ## Run isort on local machine.
	poetry run isort --atomic . 

.PHONY: restyle
restyle: black isort ## Run all black an isort on local machine.

.PHONY: battery
battery: style-check static-check ## Run all checks
	printf "\nPassed all checks...\n"
