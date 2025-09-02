# Test-Driven Development Setup for Odoo MCP

This document describes the TDD framework setup for the Odoo MCP Server project.

## Overview

The project uses a comprehensive TDD approach with:
- **pytest** as the testing framework
- **pytest-asyncio** for async test support
- **Real Odoo API** testing (no mocks)
- **Pre-commit hooks** for code quality
- **UV** as the package manager

## Directory Structure

```
tests/
├── unit/           # Fast, isolated unit tests
├── integration/    # Tests that connect to Odoo API
├── e2e/           # End-to-end workflow tests
└── conftest.py    # Shared fixtures and configuration
```

## Configuration Files

### pyproject.toml
- Python 3.13+ requirement
- All dependencies with UV support
- Ruff linting configuration
- MyPy strict type checking
- pytest configuration

### .pre-commit-config.yaml
Pre-commit hooks that run automatically:
- **ruff**: Fast Python linting and formatting
- **mypy**: Type checking with strict mode
- **bandit**: Security vulnerability scanning
- **safety**: Dependency vulnerability checking
- **detect-secrets**: Prevent credential leaks
- **pytest**: Quick unit tests before push

### pytest.ini
- Async mode enabled by default
- Coverage requirements (90% minimum)
- Parallel test execution
- Custom markers for test categories

## Environment Setup

1. **Install UV** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Install dependencies**:
   ```bash
   uv pip install -e ".[dev]"
   ```

3. **Install pre-commit hooks**:
   ```bash
   pre-commit install
   pre-commit install --hook-type commit-msg
   ```

4. **Configure environment**:
   - Copy `.env.example` to `.env`
   - Set Odoo test instance credentials

## Running Tests

### All tests:
```bash
make test
# or
uv run pytest
```

### Unit tests only:
```bash
make test-unit
# or
uv run pytest tests/unit -v
```

### Integration tests:
```bash
make test-integration
# or
uv run pytest tests/integration -v -m integration
```

### E2E tests:
```bash
make test-e2e
# or
uv run pytest tests/e2e -v -m e2e
```

### With coverage:
```bash
make test-cov
# or
uv run pytest --cov=src --cov-report=html
```

## Test Fixtures

### odoo_connection
- Provides authenticated connection to test Odoo instance
- Automatically cleans up created test data
- Tracks all created records for cleanup

### Test Data Fixtures
- `test_partner_data`: Sample partner/customer data
- `test_product_data`: Sample product data
- `test_sale_order_data`: Sample sale order data

### Helper Functions
- `create_test_record()`: Create and track test records
- `read_test_record()`: Read records with field selection
- `search_test_records()`: Search with Odoo domain syntax
- `delete_test_record()`: Manual record deletion

## Writing Tests

### Unit Test Example
```python
@pytest.mark.unit
async def test_data_validation() -> None:
    """Test data validation logic."""
    # No external dependencies
    assert validate_email("test@example.com") is True
```

### Integration Test Example
```python
@pytest.mark.integration
@pytest.mark.odoo
async def test_create_partner(odoo_connection: OdooTestConnection) -> None:
    """Test creating a partner in Odoo."""
    partner_id = await create_test_record(
        odoo_connection, 
        "res.partner", 
        {"name": "Test Partner"}
    )
    assert partner_id > 0
    # Cleanup is automatic
```

### E2E Test Example
```python
@pytest.mark.e2e
@pytest.mark.slow
async def test_procurement_workflow(odoo_connection: OdooTestConnection) -> None:
    """Test complete procurement workflow."""
    # Multi-step workflow testing
    # Real API calls throughout
```

## Code Quality

### Pre-commit Checks
Every commit automatically runs:
1. Ruff formatting and linting
2. MyPy type checking
3. Security scanning (bandit)
4. Dependency vulnerability check (safety)
5. Secret detection

### Manual Checks
```bash
# Run all pre-commit checks
make pre-commit

# Individual checks
make lint          # Ruff linting
make format        # Ruff formatting
make type-check    # MyPy
make security      # Bandit + Safety
```

## Best Practices

1. **No Mocking**: All tests use real Odoo API calls
2. **Test Isolation**: Each test gets clean state
3. **Automatic Cleanup**: Created records are tracked and deleted
4. **Type Safety**: 100% type annotation coverage
5. **Fast Feedback**: Unit tests run on every push
6. **Security First**: Pre-commit hooks catch issues early

## Continuous Integration

The test suite is designed for CI/CD:
- Parallel test execution for speed
- Coverage reporting with 90% minimum
- Separate test categories for staged testing
- Environment-based configuration

## Troubleshooting

### Connection Issues
- Verify `.env` has correct Odoo credentials
- Check network access to Odoo instance
- Ensure test database is accessible

### Test Failures
- Check for leftover test data
- Verify Odoo instance version compatibility
- Review test logs for API errors

### Pre-commit Failures
- Run `pre-commit run --all-files` to see all issues
- Use `make check-all` for comprehensive validation
- Emergency skip: `git commit --no-verify` (not recommended)