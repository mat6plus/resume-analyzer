# Makefile for Docker Compose automation

# Variables
DOCKER_COMPOSE = docker-compose
APP_NAME = resume-analyzer

# Default target
.DEFAULT_GOAL := help

# Help target
help:
	@echo "Available commands:"
	@echo "  make build      - Build Docker images"
	@echo "  make up         - Start the application"
	@echo "  make down       - Stop the application"
	@echo "  make restart    - Restart the application"
	@echo "  make logs       - View application logs"
	@echo "  make shell      - Open a shell in the application container"
	@echo "  make clean      - Remove stopped containers and unused images"

# Build Docker images
build:
	$(DOCKER_COMPOSE) build

# Start the application
up:
	$(DOCKER_COMPOSE) up -d

# Stop the application
down:
	$(DOCKER_COMPOSE) down

# Restart the application
restart: down up

# View application logs
logs:
	$(DOCKER_COMPOSE) logs -f

# Open a shell in the application container
shell:
	$(DOCKER_COMPOSE) exec $(APP_NAME) /bin/bash

# Remove stopped containers and unused images
clean:
	docker system prune -f

# Build and start the application
deploy: build up

.PHONY: help build up down restart logs shell clean deploy