from __future__ import annotations

from pydantic import BaseModel
from packaging.version import Version
from collections import OrderedDict
from typing import Any
from pathlib import Path

from .v1 import upfv1contents_to_dict
from .v2 import upfv2contents_to_dict
from .utils import get_version_number

class UPFModel(BaseModel):
    version: Version
    filename: Path | None = None
    content: OrderedDict[str, Any]

    model_config = {"arbitrary_types_allowed": True,
                    "validate_assignment": True,
                    "extra": "forbid"}

    @classmethod
    def from_str(cls, string: str) -> UPFModel:
        """Create a :class:`UPFModel` object from a string (typically the contents of a ``.upf`` file)."""
        # Fetch the version number
        version = get_version_number(string)
        # Parse the string into an OrderedDict (implementation not shown)
        if version.major == 1:
            content = upfv1contents_to_dict(string)
        elif version.major == 2:
            content = upfv2contents_to_dict(string)
        else:
            raise ValueError(f"Unsupported UPF version: {version}")
        return cls(version=version, content=content)
    
    @classmethod
    def from_upf(cls, filename: Path | str) -> UPFModel:
        """Create a :class:`UPFModel` object from a ``.upf`` file."""
        # Sanitise input
        filename = filename if isinstance(filename, Path) else Path(filename)

        # Read the file contents
        with open(filename, "r") as fd:
            flines = fd.read()

        # Use cls.from_str to construct the pseudopotential information
        upf_model = cls.from_str(flines)
        upf_model.filename = str(filename)

        return upf_model

