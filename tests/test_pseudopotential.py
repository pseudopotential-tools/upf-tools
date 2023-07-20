"""Testing the `Pseudopotential` class."""

from pathlib import Path

import pytest

from upf_tools import Pseudopotential

sssp = Path(__file__).parent / "sssp"


@pytest.mark.parametrize("filename", [f for ext in ["upf", "UPF"] for f in sssp.glob(f"*.{ext}")])
def test_from_upf(filename):
    """Tests creating a `Pseudopotential` object via the classmethod `from_upf`."""
    psp = Pseudopotential.from_upf(filename)
    assert "header" in psp
    assert "z_valence" in psp["header"]
    assert "number_of_proj" in psp["header"]
    assert "number_of_wfc" in psp["header"]
    assert "mesh" in psp
    assert "r" in psp["mesh"]
    assert "local" in psp
    assert "rhoatom" in psp
    assert psp.filename == filename


@pytest.mark.parametrize("filename", [f for ext in ["upf", "UPF"] for f in sssp.glob(f"*.{ext}")])
def test_to_dat(filename):
    """Tests creating a `Pseudopotential` object via the classmethod `from_upf`."""
    psp = Pseudopotential.from_upf(filename)
    psp.to_dat()
