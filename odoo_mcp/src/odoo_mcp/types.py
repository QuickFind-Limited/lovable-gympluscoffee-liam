"""Type definitions for Odoo MCP server."""

from typing import Any, Literal, TypeAlias, TypedDict

# Basic Odoo types
OdooId: TypeAlias = int
OdooIds: TypeAlias = list[int]

# Odoo record type
OdooRecord: TypeAlias = dict[str, Any]

# Search domain types
OdooOperator: TypeAlias = Literal[
    "=",
    "!=",
    "<",
    "<=",
    ">",
    ">=",
    "like",
    "ilike",
    "not like",
    "not ilike",
    "in",
    "not in",
    "child_of",
    "parent_of",
]

OdooLogicalOperator: TypeAlias = Literal["&", "|", "!"]

OdooDomainTuple: TypeAlias = tuple[str, OdooOperator, Any]
OdooDomainElement: TypeAlias = OdooDomainTuple | OdooLogicalOperator
OdooSearchDomain: TypeAlias = list[OdooDomainElement]

# Context type
OdooContext: TypeAlias = dict[str, Any]


# Error type
class OdooError(TypedDict):
    """Odoo error structure."""

    message: str
    code: int
    data: dict[str, Any]


# Method parameters
class OdooMethodParams(TypedDict):
    """Parameters for Odoo method calls."""

    model: str
    method: str
    args: list[Any]
    kwargs: dict[str, Any] | None


# Server context type
class ServerContext(TypedDict):
    """Server context containing initialized components."""

    connection_pool: Any  # ConnectionPoolManager
    tool_registry: Any  # ToolRegistry
    resource_handler: Any  # ResourceHandler


# MCP tool parameter types
class CreateParams(TypedDict):
    """Parameters for create tool."""

    instance_id: str
    model: str
    values: dict[str, Any]


class ReadParams(TypedDict):
    """Parameters for read tool."""

    instance_id: str
    model: str
    ids: list[int]
    fields: list[str] | None


class SearchParams(TypedDict):
    """Parameters for search tool."""

    instance_id: str
    model: str
    domain: OdooSearchDomain
    limit: int | None
    offset: int | None
    order: str | None


class SearchReadParams(TypedDict):
    """Parameters for search_read tool."""

    instance_id: str
    model: str
    domain: OdooSearchDomain
    fields: list[str] | None
    limit: int | None
    offset: int | None
    order: str | None


class UpdateParams(TypedDict):
    """Parameters for update tool."""

    instance_id: str
    model: str
    ids: list[int]
    values: dict[str, Any]


class DeleteParams(TypedDict):
    """Parameters for delete tool."""

    instance_id: str
    model: str
    ids: list[int]


# Validation functions
def validate_search_domain(domain: Any) -> bool:
    """Validate an Odoo search domain.

    Args:
        domain: Domain to validate

    Returns:
        True if valid, False otherwise
    """
    if not isinstance(domain, list):
        return False

    for element in domain:
        if isinstance(element, str):
            # Logical operator
            if element not in ["&", "|", "!"]:
                return False
        elif isinstance(element, (tuple, list)):
            # Domain tuple (can be list when coming from JSON)
            if len(element) != 3:
                return False
            if not isinstance(element[0], str):
                return False
            if element[1] not in [
                "=",
                "!=",
                "<",
                "<=",
                ">",
                ">=",
                "like",
                "ilike",
                "not like",
                "not ilike",
                "in",
                "not in",
                "child_of",
                "parent_of",
            ]:
                return False
        else:
            return False

    return True


def validate_record_data(data: Any) -> bool:
    """Validate Odoo record data.

    Args:
        data: Data to validate

    Returns:
        True if valid, False otherwise
    """
    if not isinstance(data, dict):
        return False

    for key, value in data.items():
        if not isinstance(key, str):
            return False

        # Check for callable values (not allowed)
        if callable(value):
            return False

        # Special handling for relation fields
        if isinstance(value, list) and value:
            # Check for x2many field commands
            for item in value:
                if isinstance(item, tuple) and len(item) >= 2:
                    command = item[0]
                    if command not in [0, 1, 2, 3, 4, 5, 6]:
                        return False

    return True


# One2many/Many2many field commands
class FieldCommand:
    """Constants for relation field commands."""

    CREATE = 0  # (0, 0, values)
    UPDATE = 1  # (1, id, values)
    DELETE = 2  # (2, id, 0)
    UNLINK = 3  # (3, id, 0)
    LINK = 4  # (4, id, 0)
    UNLINK_ALL = 5  # (5, 0, 0)
    REPLACE = 6  # (6, 0, ids)
