"""Testing the `Pseudopotential` class."""

from pathlib import Path

import pytest

from upf_tools import Pseudopotential

datadir = Path(__file__).parent / "data"


@pytest.mark.parametrize("filename", [f for f in datadir.glob("*.upf")])
def test_from_upf(filename):
    """Tests creating a `Pseudopotential` object via the classmethod `from_upf`."""
    psp = Pseudopotential.from_upf(filename)
    assert psp.filename == filename
