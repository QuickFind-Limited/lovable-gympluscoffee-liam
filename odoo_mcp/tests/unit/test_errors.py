"""Unit tests for error handling."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from typing import Any, Callable

from odoo_mcp.errors import (
    OdooMCPError,
    ConnectionError,
    AuthenticationError,
    PermissionError,
    ValidationError,
    NotFoundError,
    RateLimitError,
    TimeoutError,
    ErrorCode,
    ErrorHandler,
    with_retry,
    format_error_response,
    parse_odoo_error,
)


class TestErrorTypes:
    """Test custom error types."""

    def test_base_error(self) -> None:
        """Test base OdooMCPError."""
        error = OdooMCPError(
            "Something went wrong",
            ErrorCode.UNKNOWN,
            {"detail": "Additional info"},
        )
        
        assert str(error) == "Something went wrong"
        assert error.code == ErrorCode.UNKNOWN
        assert error.details == {"detail": "Additional info"}

    def test_connection_error(self) -> None:
        """Test ConnectionError."""
        error = ConnectionError(
            "Failed to connect to Odoo",
            {"url": "https://odoo.example.com"},
        )
        
        assert str(error) == "Failed to connect to Odoo"
        assert error.code == ErrorCode.CONNECTION_ERROR
        assert error.details["url"] == "https://odoo.example.com"

    def test_authentication_error(self) -> None:
        """Test AuthenticationError."""
        error = AuthenticationError(
            "Invalid credentials",
            {"username": "admin"},
        )
        
        assert str(error) == "Invalid credentials"
        assert error.code == ErrorCode.AUTHENTICATION_ERROR
        assert error.details["username"] == "admin"

    def test_permission_error(self) -> None:
        """Test PermissionError."""
        error = PermissionError(
            "Access denied",
            {"model": "account.invoice", "operation": "create"},
        )
        
        assert str(error) == "Access denied"
        assert error.code == ErrorCode.PERMISSION_ERROR
        assert error.details["model"] == "account.invoice"

    def test_validation_error(self) -> None:
        """Test ValidationError."""
        error = ValidationError(
            "Invalid data",
            {"field": "email", "value": "invalid-email"},
        )
        
        assert str(error) == "Invalid data"
        assert error.code == ErrorCode.VALIDATION_ERROR
        assert error.details["field"] == "email"

    def test_not_found_error(self) -> None:
        """Test NotFoundError."""
        error = NotFoundError(
            "Record not found",
            {"model": "res.partner", "id": 999},
        )
        
        assert str(error) == "Record not found"
        assert error.code == ErrorCode.NOT_FOUND
        assert error.details["id"] == 999

    def test_rate_limit_error(self) -> None:
        """Test RateLimitError."""
        error = RateLimitError(
            "Rate limit exceeded",
            {"limit": 100, "window": "1h"},
        )
        
        assert str(error) == "Rate limit exceeded"
        assert error.code == ErrorCode.RATE_LIMIT
        assert error.details["limit"] == 100

    def test_timeout_error(self) -> None:
        """Test TimeoutError."""
        error = TimeoutError(
            "Operation timed out",
            {"timeout": 30, "operation": "search"},
        )
        
        assert str(error) == "Operation timed out"
        assert error.code == ErrorCode.TIMEOUT
        assert error.details["timeout"] == 30


class TestErrorHandler:
    """Test ErrorHandler class."""

    @pytest.fixture
    def error_handler(self) -> ErrorHandler:
        """Create error handler instance."""
        return ErrorHandler(max_retries=3, backoff_factor=2.0)

    async def test_successful_operation(self, error_handler: ErrorHandler) -> None:
        """Test retry decorator with successful operation."""
        call_count = 0
        
        @error_handler.with_retry()
        async def successful_operation() -> str:
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = await successful_operation()
        assert result == "success"
        assert call_count == 1  # No retries needed

    async def test_retry_on_timeout(self, error_handler: ErrorHandler) -> None:
        """Test retry on timeout error."""
        call_count = 0
        
        @error_handler.with_retry(retryable_errors=(asyncio.TimeoutError,))
        async def flaky_operation() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise asyncio.TimeoutError("Timeout")
            return "success"
        
        result = await flaky_operation()
        assert result == "success"
        assert call_count == 3  # Two retries

    async def test_max_retries_exceeded(self, error_handler: ErrorHandler) -> None:
        """Test max retries exceeded."""
        call_count = 0
        
        @error_handler.with_retry(retryable_errors=(ConnectionError,))
        async def always_fails() -> str:
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Connection failed")
        
        with pytest.raises(OdooMCPError) as exc_info:
            await always_fails()
        
        assert "Max retries exceeded" in str(exc_info.value)
        assert call_count == 3  # All retries attempted

    async def test_non_retryable_error(self, error_handler: ErrorHandler) -> None:
        """Test non-retryable error is not retried."""
        call_count = 0
        
        @error_handler.with_retry(retryable_errors=(asyncio.TimeoutError,))
        async def auth_failure() -> str:
            nonlocal call_count
            call_count += 1
            raise AuthenticationError("Invalid credentials")
        
        with pytest.raises(AuthenticationError):
            await auth_failure()
        
        assert call_count == 1  # No retries for non-retryable error

    async def test_exponential_backoff(self, error_handler: ErrorHandler, monkeypatch) -> None:
        """Test exponential backoff timing."""
        sleep_times = []
        
        async def mock_sleep(seconds: float) -> None:
            sleep_times.append(seconds)
        
        monkeypatch.setattr(asyncio, "sleep", mock_sleep)
        
        @error_handler.with_retry()
        async def failing_operation() -> str:
            raise asyncio.TimeoutError("Timeout")
        
        with pytest.raises(OdooMCPError):
            await failing_operation()
        
        # Check exponential backoff: 2^0=1, 2^1=2
        assert len(sleep_times) == 2
        assert sleep_times[0] == 1.0
        assert sleep_times[1] == 2.0


class TestRetryDecorator:
    """Test standalone retry decorator."""

    async def test_with_retry_decorator(self) -> None:
        """Test with_retry as standalone decorator."""
        call_count = 0
        
        @with_retry(max_retries=2, backoff_factor=1.0)
        async def operation() -> str:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionError("First attempt failed")
            return "success"
        
        result = await operation()
        assert result == "success"
        assert call_count == 2

    async def test_with_retry_custom_errors(self) -> None:
        """Test with_retry with custom retryable errors."""
        @with_retry(
            max_retries=3,
            retryable_errors=(ValueError, TypeError),
        )
        async def operation() -> str:
            raise ValueError("Custom error")
        
        with pytest.raises(OdooMCPError) as exc_info:
            await operation()
        
        assert "Max retries exceeded" in str(exc_info.value)


class TestErrorFormatting:
    """Test error formatting functions."""

    def test_format_error_response(self) -> None:
        """Test formatting error for MCP response."""
        error = ValidationError(
            "Invalid email format",
            {"field": "email", "value": "not-an-email"},
        )
        
        response = format_error_response(error)
        
        assert response["error"] == "Invalid email format"
        assert response["code"] == "E004"
        assert response["details"]["field"] == "email"
        assert response["details"]["value"] == "not-an-email"

    def test_format_standard_exception(self) -> None:
        """Test formatting standard Python exception."""
        error = ValueError("Something went wrong")
        
        response = format_error_response(error)
        
        assert response["error"] == "Something went wrong"
        assert response["code"] == "E999"  # Unknown error code
        assert response["details"]["type"] == "ValueError"

    def test_parse_odoo_error_access_error(self) -> None:
        """Test parsing Odoo access error."""
        odoo_error = {
            "message": "Access Error",
            "data": {
                "name": "odoo.exceptions.AccessError",
                "debug": "You are not allowed to access 'Invoice' (account.move) records.",
            },
        }
        
        parsed = parse_odoo_error(odoo_error)
        
        assert isinstance(parsed, PermissionError)
        assert "not allowed to access" in str(parsed)
        assert parsed.details["model"] == "account.move"

    def test_parse_odoo_error_validation(self) -> None:
        """Test parsing Odoo validation error."""
        odoo_error = {
            "message": "Validation Error",
            "data": {
                "name": "odoo.exceptions.ValidationError",
                "debug": "The field 'email' is not valid.",
                "arguments": ["email"],
            },
        }
        
        parsed = parse_odoo_error(odoo_error)
        
        assert isinstance(parsed, ValidationError)
        assert "not valid" in str(parsed)
        assert "email" in parsed.details.get("fields", [])

    def test_parse_odoo_error_missing_record(self) -> None:
        """Test parsing Odoo missing record error."""
        odoo_error = {
            "message": "Missing Record",
            "data": {
                "name": "odoo.exceptions.MissingError",
                "debug": "Record does not exist or has been deleted.",
            },
        }
        
        parsed = parse_odoo_error(odoo_error)
        
        assert isinstance(parsed, NotFoundError)
        assert "does not exist" in str(parsed)

    def test_parse_odoo_error_generic(self) -> None:
        """Test parsing generic Odoo error."""
        odoo_error = {
            "message": "Something went wrong",
            "data": {
                "name": "Exception",
                "debug": "An unexpected error occurred.",
            },
        }
        
        parsed = parse_odoo_error(odoo_error)
        
        assert isinstance(parsed, OdooMCPError)
        assert str(parsed) == "Something went wrong"
        assert parsed.code == ErrorCode.UNKNOWN
