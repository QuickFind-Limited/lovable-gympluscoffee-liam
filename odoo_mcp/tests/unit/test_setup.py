"""Unit tests to verify test setup is working correctly."""

import pytest


def test_pytest_is_working() -> None:
    """Verify that pytest is installed and working."""
    assert True


def test_python_version() -> None:
    """Verify we're using Python 3.13+."""
    import sys
    assert sys.version_info >= (3, 13)


@pytest.mark.asyncio
async def test_async_support() -> None:
    """Verify that async tests are supported."""
    import asyncio
    await asyncio.sleep(0.001)
    assert True


def test_type_annotations() -> None:
    """Verify that type annotations work correctly."""
    def typed_function(x: int, y: str) -> tuple[int, str]:
        return x, y
    
    result = typed_function(42, "test")
    assert result == (42, "test")


@pytest.mark.unit
def test_markers_work() -> None:
    """Verify that pytest markers are working."""
    assert True