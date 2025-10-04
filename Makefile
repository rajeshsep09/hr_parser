.PHONY: install dev-install start stop test clean format lint

# Install dependencies
install:
	pip install -r requirements.txt

# Install in development mode
dev-install:
	pip install -e .

# Start the application
start:
	python start_app.py

# Start with uvicorn directly
start-uvicorn:
	uvicorn src.app.main:app --reload --port 8080

# Start MongoDB
start-mongo:
	docker compose -f infra/docker-compose.yml up -d

# Stop MongoDB
stop-mongo:
	docker compose -f infra/docker-compose.yml down

# Run tests
test:
	pytest tests/

# Clean up
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

# Format code
format:
	black src/ tests/
	isort src/ tests/

# Lint code
lint:
	mypy src/
	black --check src/ tests/
	isort --check-only src/ tests/

# Full setup
setup: install dev-install start-mongo
	@echo "Setup complete! Run 'make start' to start the application."
