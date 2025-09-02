"""Error handling for Odoo MCP server."""

import asyncio
import logging
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, Optional, Type, Union, TypeVar, ParamSpec


class ErrorCode(Enum):
    """Standardized error codes."""
    CONNECTION_ERROR = "E001"
    AUTHENTICATION_ERROR = "E002"
    PERMISSION_ERROR = "E003"
    VALIDATION_ERROR = "E004"
    NOT_FOUND = "E005"
    RATE_LIMIT = "E006"
    TIMEOUT = "E007"
    UNKNOWN = "E999"


class OdooMCPError(Exception):
    """Base exception for Odoo MCP errors."""
    
    def __init__(
        self,
        message: str,
        code: ErrorCode,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize error with message, code, and optional details.
        
        Args:
            message: Error message
            code: Error code
            details: Additional error details
        """
        super().__init__(message)
        self.code = code
        self.details = details or {}


class ConnectionError(OdooMCPError):
    """Connection related errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCode.CONNECTION_ERROR, details)


class AuthenticationError(OdooMCPError):
    """Authentication related errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCode.AUTHENTICATION_ERROR, details)


class PermissionError(OdooMCPError):
    """Permission related errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCode.PERMISSION_ERROR, details)


class ValidationError(OdooMCPError):
    """Validation related errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCode.VALIDATION_ERROR, details)


class NotFoundError(OdooMCPError):
    """Resource not found errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCode.NOT_FOUND, details)


class RateLimitError(OdooMCPError):
    """Rate limit exceeded errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCode.RATE_LIMIT, details)


class TimeoutError(OdooMCPError):
    """Operation timeout errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCode.TIMEOUT, details)


class ErrorHandler:
    """Centralized error handling with retry logic."""
    
    def __init__(self, max_retries: int = 3, backoff_factor: float = 2.0):
        """Initialize error handler.
        
        Args:
            max_retries: Maximum number of retry attempts
            backoff_factor: Exponential backoff factor
        """
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.logger = logging.getLogger(__name__)
    
    def with_retry(
        self,
        retryable_errors: tuple[Type[Exception], ...] = (
            asyncio.TimeoutError,
            ConnectionError,
        )
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorator for automatic retry with exponential backoff.
        
        Args:
            retryable_errors: Tuple of exception types to retry
            
        Returns:
            Decorated function
        """
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            @wraps(func)
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                last_error = None
                
                for attempt in range(self.max_retries):
                    try:
                        return await func(*args, **kwargs)
                    except retryable_errors as e:
                        last_error = e
                        if attempt < self.max_retries - 1:
                            delay = self.backoff_factor ** attempt
                            self.logger.warning(
                                f"Retry {attempt + 1}/{self.max_retries} "
                                f"after {delay}s: {str(e)}"
                            )
                            await asyncio.sleep(delay)
                        else:
                            raise OdooMCPError(
                                f"Max retries exceeded: {str(e)}",
                                ErrorCode.CONNECTION_ERROR,
                                {"original_error": str(e)}
                            )
                
                # This should not be reached, but just in case
                if last_error:
                    raise last_error
                    
            return wrapper
        return decorator


def with_retry(
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    retryable_errors: tuple[Type[Exception], ...] = (
        asyncio.TimeoutError,
        ConnectionError,
    )
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Standalone retry decorator.
    
    Args:
        max_retries: Maximum number of retry attempts
        backoff_factor: Exponential backoff factor
        retryable_errors: Tuple of exception types to retry
        
    Returns:
        Decorator function
    """
    handler = ErrorHandler(max_retries=max_retries, backoff_factor=backoff_factor)
    return handler.with_retry(retryable_errors=retryable_errors)


def format_error_response(error: Union[OdooMCPError, Exception]) -> Dict[str, Any]:
    """Format error for MCP response.
    
    Args:
        error: Error to format
        
    Returns:
        Formatted error dictionary
    """
    if isinstance(error, OdooMCPError):
        return {
            "error": str(error),
            "code": error.code.value,
            "details": error.details,
        }
    else:
        # Handle standard exceptions
        return {
            "error": str(error),
            "code": ErrorCode.UNKNOWN.value,
            "details": {
                "type": type(error).__name__,
            },
        }


def parse_odoo_error(error_data: Dict[str, Any]) -> OdooMCPError:
    """Parse Odoo error response into appropriate exception.
    
    Args:
        error_data: Error data from Odoo
        
    Returns:
        Appropriate OdooMCPError subclass
    """
    message = error_data.get("message", "Unknown error")
    data = error_data.get("data", {})
    error_name = data.get("name", "")
    debug = data.get("debug", "")
    
    # Map Odoo exceptions to our error types
    if "AccessError" in error_name or "not allowed to access" in debug:
        details = {"model": "unknown"}
        # Try to extract model name from debug message
        if "(" in debug and ")" in debug:
            start = debug.rfind("(")
            end = debug.rfind(")")
            if start != -1 and end != -1:
                details["model"] = debug[start+1:end]
        return PermissionError(debug or message, details)
    
    elif "ValidationError" in error_name:
        details = {}
        if "arguments" in data:
            details["fields"] = data["arguments"]
        return ValidationError(debug or message, details)
    
    elif "MissingError" in error_name:
        return NotFoundError(debug or message)
    
    elif "UserError" in error_name:
        return ValidationError(debug or message)
    
    else:
        # Generic error
        return OdooMCPError(
            message,
            ErrorCode.UNKNOWN,
            {"debug": debug, "name": error_name}
        )
