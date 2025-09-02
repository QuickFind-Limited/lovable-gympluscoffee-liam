"""Unit tests for type definitions."""

import pytest
from typing import Any, Dict, List, Optional

from odoo_mcp.types import (
    OdooRecord,
    OdooSearchDomain,
    OdooContext,
    OdooError,
    OdooMethodParams,
    validate_search_domain,
    validate_record_data,
)


class TestOdooTypes:
    """Test Odoo type definitions and validation."""

    def test_odoo_record_type(self) -> None:
        """Test OdooRecord type definition."""
        record: OdooRecord = {
            "id": 1,
            "name": "Test Partner",
            "email": "test@example.com",
            "is_company": False,
            "child_ids": [2, 3],
        }
        
        assert record["id"] == 1
        assert record["name"] == "Test Partner"
        assert isinstance(record["child_ids"], list)

    def test_odoo_search_domain_simple(self) -> None:
        """Test simple search domain."""
        domain: OdooSearchDomain = [
            ("name", "=", "Test Partner"),
            ("is_company", "=", True),
        ]
        
        assert len(domain) == 2
        assert domain[0][0] == "name"
        assert domain[0][1] == "="
        assert domain[0][2] == "Test Partner"

    def test_odoo_search_domain_complex(self) -> None:
        """Test complex search domain with operators."""
        domain: OdooSearchDomain = [
            "|",
            ("name", "ilike", "test"),
            "&",
            ("email", "!=", False),
            ("is_company", "=", True),
        ]
        
        assert domain[0] == "|"
        assert domain[2] == "&"
        assert isinstance(domain[1], tuple)
        assert len(domain[1]) == 3

    def test_odoo_context_type(self) -> None:
        """Test OdooContext type definition."""
        context: OdooContext = {
            "lang": "en_US",
            "tz": "UTC",
            "uid": 2,
            "active_model": "res.partner",
            "active_ids": [1, 2, 3],
        }
        
        assert context["lang"] == "en_US"
        assert isinstance(context["active_ids"], list)

    def test_odoo_error_type(self) -> None:
        """Test OdooError type definition."""
        error: OdooError = {
            "message": "Access denied",
            "code": 403,
            "data": {
                "name": "AccessError",
                "debug": "You don't have access to this record",
            },
        }
        
        assert error["message"] == "Access denied"
        assert error["code"] == 403
        assert error["data"]["name"] == "AccessError"

    def test_odoo_method_params(self) -> None:
        """Test OdooMethodParams type definition."""
        params: OdooMethodParams = {
            "model": "res.partner",
            "method": "create",
            "args": [{"name": "Test Partner"}],
            "kwargs": {"context": {"lang": "en_US"}},
        }
        
        assert params["model"] == "res.partner"
        assert params["method"] == "create"
        assert isinstance(params["args"], list)
        assert isinstance(params["kwargs"], dict)


class TestValidation:
    """Test validation functions."""

    def test_validate_search_domain_valid(self) -> None:
        """Test validation of valid search domains."""
        # Simple domain
        assert validate_search_domain([("name", "=", "Test")]) is True
        
        # Complex domain with operators
        assert validate_search_domain([
            "|",
            ("name", "ilike", "test"),
            ("email", "!=", False),
        ]) is True
        
        # Empty domain
        assert validate_search_domain([]) is True

    def test_validate_search_domain_invalid(self) -> None:
        """Test validation of invalid search domains."""
        # Invalid tuple length
        assert validate_search_domain([("name", "=")]) is False
        
        # Invalid operator position
        assert validate_search_domain([("|", "name", "=")]) is False
        
        # Invalid type
        assert validate_search_domain([{"name": "Test"}]) is False
        
        # Mixed valid and invalid
        assert validate_search_domain([
            ("name", "=", "Test"),
            "invalid",
        ]) is False

    def test_validate_record_data_valid(self) -> None:
        """Test validation of valid record data."""
        # Simple record
        assert validate_record_data({"name": "Test"}) is True
        
        # Complex record
        assert validate_record_data({
            "name": "Test Partner",
            "email": "test@example.com",
            "child_ids": [(0, 0, {"name": "Child"})],
            "category_id": [(6, 0, [1, 2, 3])],
        }) is True
        
        # Empty record
        assert validate_record_data({}) is True

    def test_validate_record_data_invalid(self) -> None:
        """Test validation of invalid record data."""
        # Not a dictionary
        assert validate_record_data("invalid") is False
        assert validate_record_data([]) is False
        assert validate_record_data(None) is False
        
        # Contains non-string keys
        assert validate_record_data({1: "value"}) is False
        
        # Contains callable values (not allowed)
        assert validate_record_data({"name": lambda x: x}) is False

    def test_validate_record_data_special_fields(self) -> None:
        """Test validation of special Odoo fields."""
        # One2many field operations
        assert validate_record_data({
            "line_ids": [
                (0, 0, {"name": "New line"}),  # Create
                (1, 42, {"name": "Update line"}),  # Update
                (2, 43, 0),  # Delete
                (3, 44, 0),  # Unlink
                (4, 45, 0),  # Link
                (5, 0, 0),  # Unlink all
                (6, 0, [46, 47]),  # Replace
            ]
        }) is True
        
        # Many2many field operations
        assert validate_record_data({
            "tag_ids": [
                (3, 10, 0),  # Unlink
                (4, 11, 0),  # Link
                (6, 0, [12, 13, 14]),  # Replace
            ]
        }) is True
