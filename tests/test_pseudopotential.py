"""Testing the `Pseudopotential` class."""

from pathlib import Path

import pytest

from upf_tools import Pseudopotential

sssp = Path(__file__).parent / "sssp"


@pytest.mark.parametrize("filename", [f for ext in ["upf", "UPF"] for f in sssp.glob(f"*.{ext}")])
def test_from_upf(filename):
    """Tests creating a `Pseudopotential` object via the classmethod `from_upf`."""
    psp = Pseudopotential.from_upf(filename)
    assert "mesh" in psp
    assert "r" in psp["mesh"]
    assert "local" in psp
    assert "rhoatom" in psp
    assert psp.filename == filename
