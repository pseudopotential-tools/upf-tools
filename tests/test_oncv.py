"""Tests for the ONCV input file classes."""

from pathlib import Path

import pytest

from upf_tools.oncv import ONCVInput

oncv_input_directory = Path(__file__).parent / "oncv_inputs"


@pytest.mark.parametrize("filename", oncv_input_directory.glob("*.dat"))
def test_oncv_input(filename):
    """Test creating a :class:`ONCVInput` object from an ONCV input file."""
    ONCVInput.from_file(filename)


@pytest.mark.parametrize("filename", oncv_input_directory.glob("*.dat"))
def test_oncv_roundtrip(filename):
    """Test creating a :class:`ONCVInput` object from file, writing it back to disk, and reading it again."""
    oncv = ONCVInput.from_file(filename)
    oncv.to_file(filename.with_suffix(".rewritten.dat"))
    oncv2 = ONCVInput.from_file(filename.with_suffix(".rewritten.dat"))
    assert oncv == oncv2
