"""Testing the :class:`UPFDict` class."""

import pytest
from packaging.version import Version

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

    def test_to_str_roundtrip(self, upf_instance):
        """Test that ``read -> to_str -> from_str`` yields an equal :class:`UPFDict`."""
        if upf_instance.version < Version("2.0.0"):
            with pytest.raises(NotImplementedError):
                upf_instance.to_str()
            pytest.skip("v1 writing not yet implemented")
        text = upf_instance.to_str()
        assert text.startswith("<UPF")
        reparsed = UPFDict.from_str(text)
        assert upf_instance == reparsed

    def test_to_upf_writes_file(self, upf_instance, tmp_path):
        """``to_upf`` writes a file that re-parses to an equal :class:`UPFDict`."""
        if upf_instance.version < Version("2.0.0"):
            pytest.skip("v1 writing not yet implemented")
        out = upf_instance.to_upf(tmp_path / "out.upf")
        assert out.is_file()
        reparsed = UPFDict.from_upf(out)
        assert upf_instance == reparsed
