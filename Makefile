.PHONY: install lint format typecheck test run-api run-worker create-module

install:
	python -m pip install -e ".[dev]"

lint:
	ruff check .

format:
	black .
	ruff check . --fix

typecheck:
	mypy app

test:
	pytest

run-api:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

run-worker:
	celery -A app.core.celery_app.celery_app worker -l info

create-module:
	python scripts/create_module.py $(name)
