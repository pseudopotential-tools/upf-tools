"""Testing the :class:`UPFDict` class."""

import pytest

from upf_tools import UPFDict


def test_from_upf(upffile):
    """Test creating a :class:`UPFDict` object via the classmethod ``from_upf``."""
    psp = UPFDict.from_upf(upffile)
    assert "header" in psp
    assert "z_valence" in psp["header"]
    assert "number_of_proj" in psp["header"]
    assert "number_of_wfc" in psp["header"]
    assert "mesh" in psp
    assert "r" in psp["mesh"]
    assert "local" in psp
    assert "rhoatom" in psp
    assert psp.filename == upffile


@pytest.fixture
def upf_instance(upffile):
    """Create a :class:`UPFDict` object from a ``.upf`` file."""
    instance = UPFDict.from_upf(upffile)
    return instance


class TestUPFDictMethods:
    """Test the methods of the :class:`UPFDict` class."""

    def test_to_dat(self, upf_instance):
        """Test generating a ``.dat`` file via ``from_upf``."""
        upf_instance.to_dat()

    def test_to_input(self, upf_instance):
        """Test generating an ONCVPSP file via ``to_oncvpsp``."""
        if "inputfile" in upf_instance["info"]:
            if "&input" in upf_instance["info"].get("inputfile", ""):
                upf_instance.to_ld1_input()
            else:
                upf_instance.to_oncvpsp_input()
