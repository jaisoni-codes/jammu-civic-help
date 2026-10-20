.PHONY: dev dev-backend dev-frontend seed test

dev:
	@echo "Starting Bharosa Jammu Backend on port 8000..."
	python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

seed:
	@echo "Seeding database..."
	python backend/seed/seed.py

test:
	@echo "Running backend test suite..."
	pytest backend/tests -v
