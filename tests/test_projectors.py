"""Testing the :class:`Projectors` class."""

from pathlib import Path

import pytest

from upf_tools.projectors import Projectors

projector_dir = Path(__file__).parent / "projectors"


@pytest.mark.parametrize("filename", projector_dir.glob("*.dat"))
def test_projector_creation(filename):
    """Test creating a :class:`Projectors` object from a ``.dat`` file."""
    projectors = Projectors.from_file(filename)
    assert len(projectors) > 0
    projectors.plot()
