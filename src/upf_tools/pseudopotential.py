"""Module containing the `Pseudopotential` class, the core class of upf-tools."""

from __future__ import annotations

from collections import OrderedDict
from pathlib import Path
from typing import Any, Tuple, Union, Optional
import re
import warnings

from packaging.version import Version

from .xml import xmlfilecontents_to_dict
from .parse_v1 import upfv1contents_to_dict


REGEX_UPF_VERSION = re.compile(r"""
    \s*<UPF\s+version\s*="
    (?P<version>.*)">
    """, re.VERBOSE)

def get_version_number(string: str) -> Version:
    match = REGEX_UPF_VERSION.search(string)
    if match:
        return Version(match.group('version'))
    else:
        warnings.warn(f'Could not determine the UPF version. Assuming v1.0.0')
        return Version('1.0.0')

class Pseudopotential(OrderedDict):
    """Class that contains all of the information of a UPF pseudopotential file."""

    def __init__(
        self, version: Union[str, Tuple[int]], filename: Optional[Union[str, Path]] = None,  *args, **kwargs
    ):
        """Initialise a Pseudopotential object."""
        super().__init__(*args, **kwargs)
        self.filename = filename  # type: ignore
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
        if self._filename is None:
            raise AttributeError(f'{self.__class__.__name__} has not been set')
        return self._filename

    @filename.setter
    def filename(self, value: Optional[Union[str, Path]]) -> None:
        if isinstance(value, str):
            value = Path(value)
        self._filename = value

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
    def from_str(cls, string: str) -> Pseudopotential:
        """Create a Pseudopotential object from a string (typically the contents of a upf file)"""

        # Fetch the version number
        version = get_version_number(string)

        # Load the contents of the pseudopotential
        if version >= Version('2.0.0'):
            dct = xmlfilecontents_to_dict(string)
        else:
            dct = upfv1contents_to_dict(string)
        
        return cls(version, **dct)

    @classmethod
    def from_upf(cls, filename: Union[Path, str]) -> Pseudopotential:
        """Create a Pseudopotential object from a upf file."""
        # Sanitise input
        filename = filename if isinstance(filename, Path) else Path(filename)

        # Read the file contents
        with open(filename, 'r') as fd:
            flines = fd.read()

        # Use cls.from_str to construct the pseudopotential information
        psp = cls.from_str(flines)
        psp.filename = filename

        return psp

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
    
    @property
    def number_of_pswfc(self) -> int:
        """Get the number of orbitals in the pseudopotential."""

        raise NotImplementedError()
