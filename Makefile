.PHONY: format lint tests run

format:
	black .
	isort .

lint:
	mypy .
	black . --check
	isort . --check
	flake8 .

tests:
	pytest tests/unit_tests

run:
	uvicorn main:app --reload --host=0.0.0.0 --port=8000

run-dev:
	uvicorn main:app --reload --port=8000

requirements:
	pip freeze > requirements.txt