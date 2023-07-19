"""Various helpful xml-related functions for upf-tools."""

import json
from pathlib import Path
from typing import Any, Dict
from xml.etree import ElementTree  # noqa

import numpy as np
from defusedxml.ElementTree import parse as defused_parse


def sanitise(value: str) -> Any:
    """Convert an arbitrary string to an int/float/bool if it appears to be one of these."""
    try:
        value = json.loads(value)
    except json.decoder.JSONDecodeError:
        pass
    return value


def xml_to_dict(element: ElementTree.Element) -> Dict[str, Any]:
    """
    Convert an xml string to a nested Dict.

    This also contains some UPF-specific quirks, namely...
     - ignoring PP_ at the start of tags
     - storing tags with .1, .2 suffixes as lists e.g. CHI.1 and CHI.2 will be stored under "CHI" as a two-element list

    :param element: an xml element

    :return: a (possibly nested) dict
    """
    result = {k.lower(): sanitise(v) for k, v in element.attrib.items()}

    # If the element has no children, extract the contents of element.text
    if len(element) == 0:
        if element.text is not None and element.text.strip():
            if "type" in element.attrib:
                # We have an array; convert it to numpy
                typestr = element.attrib["type"]
                dtype = float if typestr == "real" else None
                value = np.array(element.text.strip().split(), dtype=dtype)
            else:
                value = element.text.strip()
            if result:
                result["content"] = value
            else:
                result = value
        return result

    # If the element has children, extract the contents of each child
    for child in element:
        child_result = xml_to_dict(child)
        tag = child.tag.split(".")[0].replace("PP_", "").lower()
        if tag in result:
            if not isinstance(result[tag], list):
                result[tag] = [result[tag]]
            result[tag].append(child_result)
        else:
            result[tag] = child_result

    return result


def xmlfile_to_dict(filename: Path):
    """Read an xml file and converts its contents into a nested dictionary."""
    root = defused_parse(filename).getroot()
    return xml_to_dict(root)
