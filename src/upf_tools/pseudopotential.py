"""Module containing the `Pseudopotential` class, the core class of upf-tools."""

from __future__ import annotations

from collections import OrderedDict
from pathlib import Path
from typing import Any, Tuple, Union

from packaging.version import Version

from .xml import xmlfile_to_dict


class Pseudopotential(OrderedDict):
    """Class that contains all of the information of a UPF pseudopotential file."""

    def __init__(
        self, filename: Union[Path, str], version: Union[str, Tuple[int]], *args, **kwargs
    ):
        """Initialise a Pseudopotential object."""
        super().__init__(*args, **kwargs)
        self.filename = filename
        self.version = version

    def __repr__(self, *args, **kwargs) -> str:
        """Provide a minimal repr of a Pseudopotential."""
        return (
            f"Pseudopotential(filename={self.filename}, version={self.version}, "
            'keys=({", ".join([k for k in self.keys()])}))'
        )

    @property
    def filename(self) -> Path:
        """The filename of the pseudopotential (including the path), protected to always be a Path."""
        return self._filename

    @filename.setter
    def filename(self, value: Union[str, Path]) -> None:
        if isinstance(value, str):
            value = Path(value)
        self._filename: Path = value

    @property
    def version(self) -> Version:
        """The UPF version of the pseudopotential file, protected to always be a Version."""
        return self._version

    @version.setter
    def version(self, value: Any) -> None:
        if not isinstance(value, Version):
            value = Version(value)
        self._version = value

    @classmethod
    def from_upf(cls, filename: Union[Path, str]) -> Pseudopotential:
        """Create a Pseudopotential object from a upf file."""
        # Sanitise input
        filename = filename if isinstance(filename, Path) else Path(filename)

        # For the moment, assume that the .upf file is xml-compatible
        dct = xmlfile_to_dict(filename)

        return cls(filename, **dct)

    def to_dat(self):
        """Generate a .dat file (containing projectors that wannier90.x can read) from a Pseudopotential object."""
        raise NotImplementedError()

    def to_oncv_input(self) -> str:
        """Extract the input file used to generate the pseudopotential (if it is present)."""
        if "inputfile" not in self["info"]:
            raise ValueError(
                f"{self.__class__.__name__} does not appear to contain input file information"
            )
        return self["info"]["inputfile"]
