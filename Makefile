.PHONY: setup dev-backend dev-frontend test test-backend test-frontend lint lint-backend lint-frontend typecheck migrate

setup:
	conda env create -f environment.yml
	pip install -r requirements.txt -r requirements-dev.txt
	cd frontend && npm install

dev-backend:
	cd backend && uvicorn app.main:app --reload

dev-frontend:
	cd frontend && npm run dev

migrate:
	cd backend && alembic upgrade head

test: test-backend test-frontend

test-backend:
	cd backend && pytest

test-frontend:
	cd frontend && npm run test

lint: lint-backend lint-frontend

lint-backend:
	cd backend && ruff check . && mypy app

lint-frontend:
	cd frontend && npm run lint && npm run typecheck
