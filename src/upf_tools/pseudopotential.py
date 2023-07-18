from __future__ import annotations
from pathlib import Path
from typing import Tuple, Union
from collections import OrderedDict
import xml.etree.ElementTree as ET
from packaging.version import Version
from upf_tools.xml import xmlfile_to_dict

class Pseudopotential(OrderedDict):
    
    """
    Class that contains all of the information of a UPF pseudopotential file
    """

    def __init__(self, filename: Union[Path, str], version: Union[str, Tuple[int]], *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.filename = filename
        self.version = version

    def __repr__(self, *args, **kwargs) -> str:
        return f'Pseudopotential(filename={self.filename}, version={self.version}, keys=({", ".join([k for k in self.keys()])}))'

    @property
    def filename(self) -> Path:
        return self._filename
    
    @filename.setter
    def filename(self, value: Union[str, Path]):
        if isinstance(value, str):
            value = Path(value)
        self._filename = value

    @property
    def version(self) -> Version:
        return self._version
    
    @version.setter
    def version(self, value):
        if not isinstance(value, Version):
            value = Version(value)
        self._version = value

    @classmethod        
    def from_upf(cls, filename: Union[Path, str]) -> Pseudopotential:
        # Sanitise input
        filename = filename if isinstance(filename, Path) else Path(filename)

        # For the moment, assume that the .upf file is xml-compatible
        dct = xmlfile_to_dict(filename)
        
        return cls(filename, **dct)

    def to_dat():
        pass

    def to_oncv_input(self):
        assert 'inputfile' in self['info']
        return self['info']['inputfile']