"""Module containing the :class:`UPFDict` class, the heart of ``upf-tools``."""

from __future__ import annotations

from collections import OrderedDict
from pathlib import Path
from typing import Any, Optional, Union

import numpy as np
from oncvpsp_tools import ONCVPSPInput
from packaging.version import Version

from .utils import get_version_number
from .v1 import upfv1contents_to_dict
from .v2 import upfv2contents_to_dict


class UPFDict(OrderedDict):
    """Class that contains all of the information of a UPF pseudopotential file.

    Note that it will usually be more convenient to create a :class:`UPFDict` object using
    the class method ``UPFDict.from_upf(...)`` i.e. ::

        from upf_tools import UPFDict
        psp = UPFDict.from_upf("/path/to/file.upf")

    instead of direct instantiation.

    :param version:  the UPF version number
    :type version:   str, Version
    :param filename: the name of the UPF file
    :param args:     arguments used to construct the dictionary of UPF entries
                     (``header``, ``mesh``, ``local``, ...)
    :param kwargs:   keyword arguments used to construct the dictionary of UPF entries

    """

    def __init__(
        self,
        version: Union[str, Version],
        filename: Optional[Union[str, Path]] = None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.filename = filename  # type: ignore
        self.version = version

    def __repr__(self, *args, **kwargs) -> str:
        """Provide a minimal representation of a UPFDict."""
        return (
            f'UPFDict(keys=({", ".join([k for k in self.keys()])}), '
            f"filename={self.filename}, version={self.version}))"
        )

    @property
    def filename(self) -> Path:
        """The filename of the pseudopotential (including the path), protected to always be a :class:`Path`."""
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
        """The UPF version of the pseudopotential file, protected to always be a :class:`Version`."""
        return self._version

    @version.setter
    def version(self, value: Any) -> None:
        if not isinstance(value, Version):
            value = Version(value)
        self._version = value

    @classmethod
    def from_str(cls, string: str) -> UPFDict:
        """Create a :class:`UPFDict` object from a string (typically the contents of a ``.upf`` file)."""
        # Fetch the version number
        version = get_version_number(string)

        # Load the contents of the pseudopotential
        if version >= Version("2.0.0"):
            dct = upfv2contents_to_dict(string)
        else:
            dct = upfv1contents_to_dict(string)

        return cls(version, **dct)

    @classmethod
    def from_upf(cls, filename: Union[Path, str]) -> UPFDict:
        """Create a :class:`UPFDict` object from a ``.upf`` file."""
        # Sanitise input
        filename = filename if isinstance(filename, Path) else Path(filename)

        # Read the file contents
        with open(filename, "r") as fd:
            flines = fd.read()

        # Use cls.from_str to construct the pseudopotential information
        psp = cls.from_str(flines)
        psp.filename = filename

        return psp

    def to_dat(self) -> str:
        """Generate a ``.dat`` file from a :class:`UPFDict` object.

        These files contain projectors that ``wannier90.x`` can read.

        :raises ValueError: The pseudopotential does not contain the pseudo-wavefunctions necessary to generate
            a ``.dat`` file

        :returns: the contents of a ``.dat`` file
        """
        # Fetch the r-mesh
        rmesh = self["mesh"]["r"]

        # Construct a logarithmic mesh
        min_r = 1e-8
        rmesh = [max(r, min_r) for r in rmesh]
        xmesh = np.log(rmesh)

        # Extract the pseudo wavefunctions, sorted by l and n
        if "chi" not in self["pswfc"]:
            raise ValueError("This pseudopotential does not contain any pseudo-wavefunctions")
        chis = sorted(self["pswfc"]["chi"], key=lambda chi: (chi["l"], chi["n"]))
        data = np.transpose([chi["content"] for chi in chis])

        dat = [f"{len(rmesh)} {len(chis)}", " ".join([str(chi["l"]) for chi in chis])]
        dat += [
            f"{x:20.15f} {r:20.15f} " + " ".join([f"{v:25.15e}" for v in row])
            for x, r, row in zip(xmesh, rmesh, data)
        ]

        return "\n".join(dat)

    def _fetch_input_block(self) -> str:
        if "inputfile" not in self["info"]:
            raise ValueError(
                f"{self.__class__.__name__} does not appear to contain input file information"
            )
        return self["info"]["inputfile"]

    def to_oncvpsp_input(self) -> ONCVPSPInput:
        """Extract the oncvpsp.x input file used to generate the pseudopotential."""
        input_str = self._fetch_input_block()
        if "&input" in input_str.lower():
            raise ValueError("This pseudopotential was generated with ld1.x, not oncvpsp.x")
        return ONCVPSPInput.from_str(input_str)

    def to_ld1_input(self) -> str:
        """Extract the ld1.x input file used to generate the pseudopotential."""
        input_str = self._fetch_input_block()
        if "&input" not in input_str.lower():
            raise ValueError("This pseudopotential does not appear to have been generated by ld1.x")
        return input_str
