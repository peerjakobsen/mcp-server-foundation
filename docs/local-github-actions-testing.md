# Local GitHub Actions Testing with act

## Overview

This document describes how to run GitHub Actions workflows locally using the `act` CLI tool, including workarounds for service container limitations and integration with docker-compose.

## act Setup and Configuration

### Installation
```bash
# macOS with Homebrew
brew install act

# Other platforms: see https://github.com/nektos/act#installation
```

### Configuration Files

1. **`.actrc`** - Main configuration:
   - Uses `catthehacker/ubuntu:act-latest` for better tool support
   - Enables verbose output and container reuse
   - Sets up secret file integration

2. **`.secrets`** - Local secrets (dummy values for testing):
   - GitHub tokens, database credentials
   - Never commit real secrets!

3. **`.env.act`** - Environment variables for local testing:
   - Development mode configurations
   - Test database URLs

## Testing Approaches

### 1. Simple Jobs (✅ Works Well)

Jobs without service dependencies work perfectly with act:

```bash
# Test basic functionality
act -W .github/workflows/local-test.yml

# Test specific job
act -W .github/workflows/local-integration.yml --job test-without-services
```

**What Works:**
- Basic Python testing with pytest
- uv package manager installation
- Code quality checks
- Environment variable handling
- Multi-step workflows

### 2. Service Container Jobs (⚠️ Limited Support)

Jobs requiring PostgreSQL/Redis services have limitations:

**act Limitations:**
- Service containers not fully supported
- `docker-compose` command not available in containers
- External service dependencies difficult to manage

**Workaround Solution:**
Use docker-compose separately to provide services:

```bash
# 1. Start services manually
docker-compose -f docker-compose.test.yml up -d postgres-test redis-test

# 2. Run tests with service connections
./scripts/test-with-services.sh

# 3. Or use act with services running externally
DATABASE_URL="postgresql://testuser:testpass@localhost:5432/testdb" \
REDIS_URL="redis://localhost:6379/0" \
act -W .github/workflows/local-integration.yml
```

## Files Created for Local Testing

### Docker Compose Configuration
- **`docker-compose.test.yml`**: PostgreSQL and Redis services for integration tests
- **`scripts/test-with-services.sh`**: Helper script to run tests with services

### Simplified Workflows
- **`.github/workflows/local-test.yml`**: Basic testing without external dependencies
- **`.github/workflows/local-integration.yml`**: Two-job workflow (with/without services)

### Configuration Files
- **`.actrc`**: act CLI configuration
- **`.secrets`**: Dummy secrets for local testing
- **`.env.act`**: Environment variables for act

## Best Practices

### 1. Workflow Design for act Compatibility

```yaml
# ✅ Good: Self-contained installation
- name: Install uv manually
  run: |
    curl -LsSf https://astral.sh/uv/install.sh | sh
    echo "$HOME/.cargo/bin" >> $GITHUB_PATH

# ❌ Problematic: External GitHub Actions
- uses: astral-sh/setup-uv@v3  # May not work in act
```

### 2. Service Container Workarounds

```yaml
# Instead of GitHub Actions services:
services:
  postgres:
    image: postgres:17
    # ... service configuration

# Use docker-compose with health checks:
- name: Start services externally
  run: |
    docker-compose -f docker-compose.test.yml up -d
    # Wait for health checks
```

### 3. Environment Variable Handling

```bash
# Use .env.act for consistent environment
DEPLOYMENT_MODE=development
DATABASE_URL=sqlite:///./data/test.db

# Override in workflows as needed
env:
  DATABASE_URL: postgresql://testuser:testpass@localhost:5432/testdb
```

## Command Reference

```bash
# Basic workflow testing
act                                    # Run default push event
act pull_request                       # Run PR workflows
act -l                                # List available jobs

# Specific workflow/job testing
act -W .github/workflows/ci.yml        # Run specific workflow
act --job test                         # Run specific job
act --job integration-test             # Run integration tests

# Debugging and configuration
act --dry-run                          # Show what would be executed
act --verbose                          # Enable verbose logging
act --reuse                            # Reuse containers (faster)

# Environment and secrets
act --env-file .env.act                # Load environment file
act --secret-file .secrets             # Load secrets file
act -s GITHUB_TOKEN=xxx                # Set individual secret
```

## Testing Results Summary

### ✅ What Works Well with act:
- Unit tests and basic functionality
- Python environments with uv/pip
- Code formatting and linting
- Environment variable management
- Multi-step bash commands
- File system operations
- Basic Docker commands

### ⚠️ What Has Limitations:
- GitHub Actions marketplace actions
- Service containers (postgres, redis, etc.)
- Complex networking between containers  
- Actions requiring GitHub API access
- Matrix builds with external dependencies

### 💡 Recommended Workflow:
1. Use act for rapid iteration on basic jobs
2. Use docker-compose + local scripts for integration tests
3. Use hybrid approach: act + external services
4. Keep one simplified workflow specifically for act testing

## Troubleshooting

### Common Issues:

1. **Port Conflicts:**
   ```bash
   # Stop conflicting containers
   docker stop $(docker ps -q --filter "publish=5432")
   ```

2. **Missing Tools in Container:**
   ```bash
   # Install tools manually in workflow steps
   - run: |
       curl -LsSf https://astral.sh/uv/install.sh | sh
       echo "$HOME/.local/bin" >> $GITHUB_PATH
   ```

3. **Service Health Checks:**
   ```bash
   # Wait for services before running tests
   - run: |
       timeout 60 bash -c 'until nc -z localhost 5432; do sleep 1; done'
   ```

4. **File Permissions:**
   ```bash
   # Make scripts executable
   chmod +x scripts/test-with-services.sh
   ```

## Conclusion

act provides excellent local testing for straightforward CI/CD workflows but requires workarounds for complex service dependencies. The combination of act + docker-compose provides a comprehensive local testing solution that covers most GitHub Actions use cases.

For this MCP server foundation project:
- ✅ Basic testing, linting, and code quality work perfectly with act
- ✅ Integration testing works with docker-compose services
- ✅ Full local CI/CD pipeline testing is achievable
- ⚠️ Some manual service management required for complex scenarios