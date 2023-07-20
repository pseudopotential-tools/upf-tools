"""Module containing the `Pseudopotential` class, the core class of upf-tools."""

from __future__ import annotations

import re
import warnings
from collections import OrderedDict
from pathlib import Path
from typing import Any, Optional, Tuple, Union

import numpy as np
from packaging.version import Version

from .v1 import upfv1contents_to_dict
from .v2 import upfv2contents_to_dict

REGEX_UPF_VERSION = re.compile(
    r"""
    \s*<UPF\s+version\s*="
    (?P<version>.*)">
    """,
    re.VERBOSE,
)


def get_version_number(string: str) -> Version:
    """Extract the version number from the contents of a UPF file."""
    match = REGEX_UPF_VERSION.search(string)
    if match:
        return Version(match.group("version"))
    else:
        warnings.warn(f"Could not determine the UPF version. Assuming v1.0.0")  # noqa
        return Version("1.0.0")


class Pseudopotential(OrderedDict):
    """Class that contains all of the information of a UPF pseudopotential file."""

    def __init__(
        self,
        version: Union[str, Tuple[int]],
        filename: Optional[Union[str, Path]] = None,
        *args,
        **kwargs,
    ):
        """
        Initialise a Pseudopotential object.

        Note that it will usually be more convenient to create a `Pseudopotential object using
        the class method `Pseudopotential.from_upf(...)`

        :param version:  the UPF version number
        :param filename: the name of the UPF file
        :param *args:    args used to construct the dictionary of UPF entries ('header', 'mesh', 'local', ...)
        :param **kwargs: kwargs used to construct the dictionary of UPF entries
        """
        super().__init__(*args, **kwargs)
        self.filename = filename  # type: ignore
        self.version = version

    def __repr__(self, *args, **kwargs) -> str:
        """Provide a minimal repr of a Pseudopotential."""
        return (
            f'Pseudopotential(keys=({", ".join([k for k in self.keys()])}), '
            f"filename={self.filename}, version={self.version}))"
        )

    @property
    def filename(self) -> Path:
        """The filename of the pseudopotential (including the path), protected to always be a Path."""
        if self._filename is None:
            raise AttributeError(f"{self.__class__.__name__} has not been set")
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
        """Create a Pseudopotential object from a string (typically the contents of a upf file)."""
        # Fetch the version number
        version = get_version_number(string)

        # Load the contents of the pseudopotential
        if version >= Version("2.0.0"):
            dct = upfv2contents_to_dict(string)
        else:
            dct = upfv1contents_to_dict(string)

        return cls(version, **dct)

    @classmethod
    def from_upf(cls, filename: Union[Path, str]) -> Pseudopotential:
        """Create a Pseudopotential object from a upf file."""
        # Sanitise input
        filename = filename if isinstance(filename, Path) else Path(filename)

        # Read the file contents
        with open(filename, "r") as fd:
            flines = fd.read()

        # Use cls.from_str to construct the pseudopotential information
        psp = cls.from_str(flines)
        psp.filename = filename

        return psp

    def to_dat(self):
        """Generate a .dat file (containing projectors that wannier90.x can read) from a Pseudopotential object."""
        # Fetch the r-mesh
        rmesh = self["mesh"]["r"]

        # Construct a logarithmic mesh
        xmesh = [np.log(max(x, 1e-8)) for x in rmesh]

        # Extract the pseudo wavefunctions, sorted by l and n
        chis = sorted(self["pswfc"]["chi"], key=lambda chi: (chi["l"], chi["n"]))
        data = np.transpose([chi["content"] for chi in chis])

        dat = [f"{len(rmesh)} {len(chis)}", " ".join([str(chi["l"]) for chi in chis])]
        dat += [
            f"{x:20.15f} {r:20.15f} " + " ".join([f"{v:25.15e}" for v in row])
            for x, r, row in zip(xmesh[1:], rmesh[1:], data[1:])
        ]

        return "\n".join(dat)

    def to_input(self) -> str:
        """Extract the input file used to generate the pseudopotential (if it is present)."""
        if "inputfile" not in self["info"]:
            raise ValueError(
                f"{self.__class__.__name__} does not appear to contain input file information"
            )
        return self["info"]["inputfile"]
