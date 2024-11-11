.ONESHELL:
SHELL := /bin/bash

.SILENT:

%:
	@:

export PYTHONPATH=.

ifndef PROMETHEUS_MULTIPROC_DIR
	export PROMETHEUS_MULTIPROC_DIR=${PWD}/.prometheus
endif

ifndef SERVICE_PORT
	export SERVICE_PORT=5000
endif

ifndef PROMETHEUS_PORT
	export PROMETHEUS_PORT=8001
endif

ifndef GUNICORN_TIMEOUT
	export GUNICORN_TIMEOUT=60
endif

ifndef GUNICORN_GRACEFUL_TIMEOUT
	export GUNICORN_GRACEFUL_TIMEOUT=20
endif

ifndef GUNICORN_WORKERS
	export GUNICORN_WORKERS=1
endif

ifndef GUNICORN_MAX_REQUESTS
	export GUNICORN_MAX_REQUESTS=1000
endif

ifndef GUNICORN_KEEP_ALIVE
	export GUNICORN_KEEP_ALIVE=5
endif


DEFAULT_GOAL := help
.PHONY: help
help:
	awk 'BEGIN {FS = ":.*?## "} /^[%a-zA-Z0-9_-]+:.*?## / {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

.PHONY: install
install: ## Create poetry environment and install all dependencies.
	poetry config virtualenvs.in-project true --local
	poetry env use 3.11
	poetry install

.PHONY: style-check
style-check: ## Run style checks.
	printf "Style Checking with Ruff\n"
	poetry run ruff check .

.PHONY: restyle
restyle: ## Reformat code with Ruff and Black.
	poetry run ruff format .
	poetry run ruff check . --fix

.PHONY: static-check
static-check: ## Run strict typing checks.
	printf "Static Checking with Mypy\n"
	poetry run mypy .

.PHONY: clean-prometheus-dir
clean-prometheus-dir: ## Clean Prometheus multiprocess directory, if exists.
	mkdir -p $(PROMETHEUS_MULTIPROC_DIR)
	rm -rf $(PROMETHEUS_MULTIPROC_DIR)/*

.PHONY: tests
tests: ## Run tests.
	printf "Tests with Pytest\n"
ifeq (plain, $(filter plain,$(MAKECMDGOALS)))
	pytest tests -s
else
	poetry run pytest -s
endif

.PHONY: battery
battery: style-check static-check tests ## Run all checks and tests
	printf "\nPassed all checks and tests...\n"

.PHONY: run.api
run.api: ## Run service with dev configuration.
ifeq (plain, $(filter plain,$(MAKECMDGOALS)))
	python serve/serve_api.py
else
	poetry run python serve/serve_api.py
endif

.PHONY: run.consumer
run.consumer: ## Run service with dev configuration.
ifeq (plain, $(filter plain,$(MAKECMDGOALS)))
	python serve/serve_consumer.py
else
	poetry run python serve/serve_consumer.py
endif

.PHONY: run.producer
run.producer: ## Run service with dev configuration.
ifeq (plain, $(filter plain,$(MAKECMDGOALS)))
	python api/producer.py
else
	poetry run python api/producer.py
endif

.PHONY: create-proto
create-proto: ## Generate proto files
ifeq (plain, $(filter plain,$(MAKECMDGOALS)))
	$(SHELL) proto_generate.sh
else
	poetry run $(SHELL) proto_generate.sh
endif

.PHONY: requirements
requirements: ## Generate requirements.txt based on poetry env.
	poetry export -f requirements.txt --output requirements.txt --without-hashes --with dev
