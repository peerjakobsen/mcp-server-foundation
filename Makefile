# Makefile for Docker operations and multi-platform builds
# Supports development and production Docker workflows

.PHONY: help
help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*##"; printf "\033[36m\033[0m"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Docker Build Commands

.PHONY: build-dev
build-dev: ## Build development Docker image
	docker build \
		--target development \
		--tag mcp-server:dev \
		--build-arg PYTHON_VERSION=3.13.6 \
		--build-arg BUILD_DATE=$(shell date -u +'%Y-%m-%dT%H:%M:%SZ') \
		--build-arg VCS_REF=$(shell git rev-parse --short HEAD) \
		--build-arg VERSION=dev \
		.

.PHONY: build-prod
build-prod: ## Build production Docker image
	docker build \
		--target production \
		--tag mcp-server:latest \
		--tag mcp-server:$(shell git describe --tags --always) \
		--build-arg PYTHON_VERSION=3.13.6 \
		--build-arg BUILD_DATE=$(shell date -u +'%Y-%m-%dT%H:%M:%SZ') \
		--build-arg VCS_REF=$(shell git rev-parse --short HEAD) \
		--build-arg VERSION=$(shell git describe --tags --always) \
		.

.PHONY: build-multi
build-multi: ## Build multi-platform images (AMD64 and ARM64)
	@echo "Setting up Docker buildx for multi-platform builds..."
	docker buildx create --name mcp-builder --use --bootstrap 2>/dev/null || docker buildx use mcp-builder
	docker buildx build \
		--platform linux/amd64,linux/arm64 \
		--target production \
		--tag mcp-server:latest \
		--tag mcp-server:$(shell git describe --tags --always) \
		--build-arg PYTHON_VERSION=3.13.6 \
		--build-arg BUILD_DATE=$(shell date -u +'%Y-%m-%dT%H:%M:%SZ') \
		--build-arg VCS_REF=$(shell git rev-parse --short HEAD) \
		--build-arg VERSION=$(shell git describe --tags --always) \
		--push=false \
		--output type=docker \
		.

.PHONY: build-and-push
build-and-push: ## Build and push multi-platform images to registry
	@echo "Building and pushing multi-platform images to GHCR..."
	docker buildx create --name mcp-builder --use --bootstrap 2>/dev/null || docker buildx use mcp-builder
	docker buildx build \
		--platform linux/amd64,linux/arm64 \
		--target production \
		--tag ghcr.io/$(GITHUB_REPOSITORY):latest \
		--tag ghcr.io/$(GITHUB_REPOSITORY):$(shell git describe --tags --always) \
		--build-arg PYTHON_VERSION=3.13.6 \
		--build-arg BUILD_DATE=$(shell date -u +'%Y-%m-%dT%H:%M:%SZ') \
		--build-arg VCS_REF=$(shell git rev-parse --short HEAD) \
		--build-arg VERSION=$(shell git describe --tags --always) \
		--push \
		.

##@ Docker Compose Commands

.PHONY: up
up: ## Start all services with docker-compose
	@mkdir -p data/postgres data/redis data/minio data/storage
	docker-compose up -d

.PHONY: up-dev
up-dev: ## Start development environment with hot reload
	@mkdir -p data/postgres data/redis data/minio data/storage
	docker-compose up

.PHONY: down
down: ## Stop and remove all containers
	docker-compose down

.PHONY: down-volumes
down-volumes: ## Stop containers and remove volumes
	docker-compose down -v

.PHONY: logs
logs: ## Show logs from all services
	docker-compose logs -f

.PHONY: logs-app
logs-app: ## Show logs from MCP server only
	docker-compose logs -f mcp-server

.PHONY: restart
restart: ## Restart all services
	docker-compose restart

.PHONY: ps
ps: ## Show running containers
	docker-compose ps

##@ Development Commands

.PHONY: shell
shell: ## Open shell in MCP server container
	docker-compose exec mcp-server /bin/bash

.PHONY: python
python: ## Open Python REPL in MCP server container
	docker-compose exec mcp-server python

.PHONY: test-docker
test-docker: ## Run Docker tests
	docker-compose -f docker-compose.test.yml up --build test-runner

.PHONY: debug
debug: ## Start with debug tools (Adminer, Redis Commander)
	docker-compose --profile debug up -d

.PHONY: storage
storage: ## Start with MinIO storage service
	docker-compose --profile storage up -d

##@ Database Commands

.PHONY: db-shell
db-shell: ## Open PostgreSQL shell
	docker-compose exec postgres psql -U mcp -d mcp_dev

.PHONY: db-backup
db-backup: ## Backup PostgreSQL database
	@mkdir -p backups
	docker-compose exec postgres pg_dump -U mcp mcp_dev > backups/mcp_dev_$(shell date +%Y%m%d_%H%M%S).sql

.PHONY: db-restore
db-restore: ## Restore PostgreSQL database from latest backup
	@latest_backup=$$(ls -t backups/*.sql | head -1); \
	if [ -z "$$latest_backup" ]; then \
		echo "No backup found in backups/"; \
		exit 1; \
	fi; \
	echo "Restoring from $$latest_backup..."; \
	docker-compose exec -T postgres psql -U mcp mcp_dev < $$latest_backup

##@ Testing Commands

.PHONY: test
test: ## Run all tests in Docker
	docker-compose run --rm mcp-server pytest

.PHONY: test-coverage
test-coverage: ## Run tests with coverage report
	docker-compose run --rm mcp-server pytest --cov=src --cov-report=html --cov-report=term

.PHONY: lint
lint: ## Run linting in Docker
	docker-compose run --rm mcp-server ruff check .

.PHONY: format
format: ## Format code in Docker
	docker-compose run --rm mcp-server ruff format .

.PHONY: type-check
type-check: ## Run type checking with mypy
	docker-compose run --rm mcp-server mypy src/

##@ Security Commands

.PHONY: scan
scan: ## Scan Docker image for vulnerabilities
	@echo "Scanning production image for vulnerabilities..."
	docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
		aquasec/trivy image mcp-server:latest

.PHONY: scan-deps
scan-deps: ## Scan dependencies for vulnerabilities
	docker-compose run --rm mcp-server safety check

.PHONY: scan-code
scan-code: ## Scan code for security issues
	docker-compose run --rm mcp-server bandit -r src/

##@ Cleanup Commands

.PHONY: clean
clean: ## Clean up Docker artifacts
	docker-compose down -v
	docker system prune -f
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true

.PHONY: clean-images
clean-images: ## Remove all MCP server Docker images
	docker images | grep mcp-server | awk '{print $$3}' | xargs -r docker rmi -f

.PHONY: clean-all
clean-all: clean clean-images ## Complete cleanup of Docker environment
	rm -rf data/postgres data/redis data/minio data/storage
	@echo "All Docker artifacts cleaned"

##@ Utility Commands

.PHONY: info
info: ## Show Docker and system information
	@echo "Docker version:"
	@docker --version
	@echo "\nDocker Compose version:"
	@docker-compose --version
	@echo "\nDocker buildx version:"
	@docker buildx version
	@echo "\nAvailable platforms:"
	@docker buildx ls
	@echo "\nCurrent images:"
	@docker images | grep mcp-server || echo "No MCP server images found"

.PHONY: init
init: ## Initialize project for Docker development
	@echo "Initializing Docker development environment..."
	@mkdir -p data/postgres data/redis data/minio data/storage backups
	@cp -n .env.example .env 2>/dev/null || true
	@echo "Creating docker volumes..."
	@docker volume create mcp_postgres_data 2>/dev/null || true
	@docker volume create mcp_redis_data 2>/dev/null || true
	@docker volume create mcp_minio_data 2>/dev/null || true
	@echo "Setting up Docker buildx for multi-platform builds..."
	@docker buildx create --name mcp-builder --use --bootstrap 2>/dev/null || true
	@echo "Initialization complete!"

# Default target
.DEFAULT_GOAL := help
