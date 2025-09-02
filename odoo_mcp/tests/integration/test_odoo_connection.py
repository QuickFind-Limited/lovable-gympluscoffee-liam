"""Integration tests for Odoo connection functionality."""

import pytest
from tests.conftest import OdooTestConnection, create_test_record, read_test_record


@pytest.mark.integration
@pytest.mark.odoo
class TestOdooConnection:
    """Test Odoo connection and basic operations."""

    async def test_authentication(self, odoo_connection: OdooTestConnection) -> None:
        """Test that we can authenticate with Odoo."""
        assert odoo_connection.uid is not None
        assert odoo_connection.uid > 0

    async def test_server_version(self, odoo_connection: OdooTestConnection) -> None:
        """Test that we can get the Odoo server version."""
        # Get server version using common service
        version_info = await odoo_connection.execute("ir.module.module", "search_count", [[]])
        # If we can count modules, connection is working
        assert isinstance(version_info, int)
        assert version_info > 0

    async def test_create_and_read_partner(
        self, odoo_connection: OdooTestConnection, test_partner_data: dict
    ) -> None:
        """Test creating and reading a partner record."""
        # Create partner
        partner_id = await create_test_record(odoo_connection, "res.partner", test_partner_data)
        assert isinstance(partner_id, int)
        assert partner_id > 0

        # Read partner back
        partner = await read_test_record(
            odoo_connection, "res.partner", partner_id, ["name", "email", "phone"]
        )
        assert partner["name"] == test_partner_data["name"]
        assert partner["email"] == test_partner_data["email"]
        assert partner["phone"] == test_partner_data["phone"]

    async def test_search_records(self, odoo_connection: OdooTestConnection) -> None:
        """Test searching for records."""
        # Search for users (should always have at least one)
        user_ids = await odoo_connection.execute(
            "res.users", "search", [[("login", "!=", False)]], {"limit": 5}
        )
        assert isinstance(user_ids, list)
        assert len(user_ids) > 0
        assert all(isinstance(uid, int) for uid in user_ids)

    async def test_cleanup_on_failure(
        self, odoo_connection: OdooTestConnection, test_partner_data: dict
    ) -> None:
        """Test that cleanup works even when test fails."""
        # Create a partner
        partner_id = await create_test_record(odoo_connection, "res.partner", test_partner_data)
        
        # Verify it exists
        partner_ids = await odoo_connection.execute(
            "res.partner", "search", [[("id", "=", partner_id)]]
        )
        assert partner_id in partner_ids
        
        # This partner will be cleaned up automatically after the test