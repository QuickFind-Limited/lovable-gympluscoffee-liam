# ADR-004: Real Testing Against Actual Odoo Instance

## Status
Accepted

## Context
Testing strategies for API integrations typically involve mocking external services. However, mocked tests often miss real-world edge cases, API changes, and integration issues. The PRD specifically requires testing against a real Odoo instance (source2.odoo.com).

## Decision
Implement testing strategy using:
- Real Odoo test instance with empty database
- No mocking of Odoo API calls
- Isolated test data per test run
- Parallel test execution with data isolation
- Property-based testing for edge cases

## Consequences

### Positive
- Tests verify actual Odoo compatibility
- Catches real API behavior and errors
- No mock maintenance burden
- Confidence in production deployments
- Early detection of Odoo API changes

### Negative
- Slower test execution
- Requires network connectivity
- Test data cleanup complexity
- Potential for flaky tests
- Dependency on external service

### Mitigation
- Parallel test execution for speed
- Proper test isolation and cleanup
- Retry logic for transient failures
- Clear test data management
- Local Odoo instance option for offline development

## Implementation Details

```python
@pytest.fixture
async def odoo_test_client(odoo_test_config):
    """Provide real Odoo client for testing."""
    pool = ConnectionPoolManager()
    await pool.add_connection("test", odoo_test_config)
    
    async with pool.get_connection("test") as client:
        # Ensure clean state
        await cleanup_test_data(client)
        yield client
        # Cleanup after test
        await cleanup_test_data(client)

@pytest.mark.integration
async def test_real_crud_operations(odoo_test_client):
    """Test against real Odoo instance."""
    # Create real record
    partner_id = await odoo_test_client.execute_kw(
        'res.partner',
        'create',
        [{'name': f'Test Partner {uuid.uuid4()}'}]
    )
    
    # Verify it exists in Odoo
    partners = await odoo_test_client.execute_kw(
        'res.partner',
        'read',
        [[partner_id]]
    )
    assert partners[0]['id'] == partner_id
```

## Test Environment Setup

```yaml
# .github/workflows/test.yml
env:
  ODOO_TEST_URL: https://source2.odoo.com
  ODOO_TEST_DB: source2
  ODOO_TEST_USER: ${{ secrets.ODOO_TEST_USER }}
  ODOO_TEST_PASSWORD: ${{ secrets.ODOO_TEST_PASSWORD }}
```

## References
- [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio)
- [Hypothesis for property testing](https://hypothesis.works/)
- [Odoo test database setup](https://www.odoo.com/documentation/17.0/developer/reference/testing.html)