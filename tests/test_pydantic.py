import pytest
from pathlib import Path

from upf_tools.pydantic import UPFModel

def test_model_from_upf(upffile: Path):
    model = UPFModel.from_upf(upffile)
    assert "header" in model.content
    assert model.version is not None
    assert model.filename == upffile


