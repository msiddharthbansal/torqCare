.PHONY: help setup data train build up down logs clean

help:
	@echo "TorqCare - Make Commands"
	@echo "========================"
	@echo "setup     - Install all dependencies"
	@echo "data      - Generate mock data"
	@echo "train     - Train ML models"
	@echo "build     - Build Docker containers"
	@echo "up        - Start all services"
	@echo "down      - Stop all services"
	@echo "logs      - View container logs"
	@echo "clean     - Remove all containers and volumes"

setup:
	@echo "📦 Installing backend dependencies..."
	cd backend && pip install -r requirements.txt
	@echo "📦 Installing frontend dependencies..."
	cd frontend && npm install
	@echo "✅ Setup complete!"

data:
	@echo "📊 Generating mock data..."
	python backend/utils/data_generator.py
	@echo "✅ Data generation complete!"

train:
	@echo "🤖 Training ML models..."
	python ml_models/train_models.py
	@echo "✅ Model training complete!"

build:
	@echo "🐳 Building Docker containers..."
	docker-compose build
	@echo "✅ Build complete!"

up:
	@echo "🚀 Starting TorqCare services..."
	docker-compose up -d
	@echo "✅ Services started!"
	@echo "Frontend: http://localhost:3000"
	@echo "Backend API: http://localhost:8000"
	@echo "API Docs: http://localhost:8000/docs"
	@echo "pgAdmin: http://localhost:5050"

down:
	@echo "🛑 Stopping TorqCare services..."
	docker-compose down
	@echo "✅ Services stopped!"

logs:
	docker-compose logs -f

clean:
	@echo "🧹 Cleaning up..."
	docker-compose down -v
	rm -rf backend/data/*.csv
	rm -rf ml_models/trained_models/*.pkl
	@echo "✅ Cleanup complete!"