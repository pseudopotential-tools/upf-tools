"""Fixtures used in the test suite."""

from pathlib import Path

import pytest

sssp = Path(__file__).parent / "sssp"


@pytest.fixture(
    params=[f for ext in ["upf", "UPF"] for f in sssp.glob(f"*.{ext}")], ids=lambda f: f.name
)
def upffile(request) -> Path:
    """Return the path to a UPF pseudopotential file."""
    return request.param
