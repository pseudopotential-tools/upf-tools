import pytest
from pathlib import Path

sssp = Path(__file__).parent / "sssp"

@pytest.fixture(params=[f for ext in ["upf", "UPF"] for f in sssp.glob(f"*.{ext}")], ids=lambda f: f.name)
def upffile(request) -> Path:
    return request.param