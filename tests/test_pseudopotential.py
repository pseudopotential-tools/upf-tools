from pathlib import Path

import pytest

from upf_tools import Pseudopotential


@pytest.mark.parametrize("filename", Path("data").glob("*.upf"))
def test_from_upf(filename):
    psp = Pseudopotential.from_upf(filename)
    assert psp.filename == filename
