"""Tests for the ONCV classes."""

from pathlib import Path

import pytest

from upf_tools.oncv import ONCVInput, ONCVOutput

oncv_directory = Path(__file__).parent / "oncv"


@pytest.mark.parametrize("filename", oncv_directory.glob("*.in"))
def test_oncv_input(filename):
    """Test creating a :class:`ONCVInput` object from an ONCV input file."""
    ONCVInput.from_file(filename)


@pytest.mark.parametrize("filename", oncv_directory.glob("*.in"))
def test_oncv_input_roundtrip(filename):
    """Test creating a :class:`ONCVInput` object from file, writing it back to disk, and reading it again."""
    oncv = ONCVInput.from_file(filename)
    oncv.to_file(filename.with_suffix(".rewritten.in"))
    oncv2 = ONCVInput.from_file(filename.with_suffix(".rewritten.in"))
    assert oncv == oncv2


@pytest.mark.parametrize("filename", oncv_directory.glob("*.out"))
def test_oncv_output(filename):
    """Test creating a :class:`ONCVOutput` object from an ONCV input file."""
    oncvo = ONCVOutput.from_file(filename)
    oncvo.charge_densities.plot()
