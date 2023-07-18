import json
import xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np


def sanitise(value):
    try:
        value = json.loads(value)
    except json.decoder.JSONDecodeError:
        pass
    return value


def xml_to_dict(element):
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
        else:
            return result if result else None

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
    root = ET.parse(filename).getroot()
    return xml_to_dict(root)
