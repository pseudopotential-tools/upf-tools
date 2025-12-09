"""Testing the :class:`UPFModel` class."""

from pathlib import Path

from upf_tools.pydantic import UPFModel


def test_model_from_upf(upffile: Path):
    """Test creating a :class:`UPFModel` object via the classmethod ``from_upf``."""
    model = UPFModel.from_upf(upffile)
    assert "header" in model.content
    assert model.version is not None
    assert model.filename == upffile
