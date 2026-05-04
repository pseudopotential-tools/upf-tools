"""Various helpful xml-related functions for upf-tools."""

from __future__ import annotations

from collections import OrderedDict
from typing import Any, Mapping
from xml.etree import ElementTree  # noqa

import numpy as np
from defusedxml.ElementTree import fromstring as defused_fromstring

from upf_tools.utils import sanitise

# Attributes that ``block_to_dict`` strips on read but that need to be
# reconstructed on write. The convention used by Quantum ESPRESSO is to
# always emit them for numeric arrays.
_ARRAY_ATTRS = ("type", "size", "columns")
_DEFAULT_COLUMNS = 4
# Tags whose children are always emitted as ``.1``, ``.2``, ... numbered
# elements when they appear as a list. The parser collapses these on
# read; ``chi`` is special-cased there to always become a list even when
# there is only one entry, so it is special-cased here too.
_ALWAYS_LIST_AS_INDEXED = {"chi"}


def block_to_dict(element: ElementTree.Element) -> OrderedDict[str, Any]:
    """
    Convert an xml string to a nested Dict.

    This also contains some UPF-specific quirks, namely...
     - ignoring PP_ at the start of tags
     - storing tags with .1, .2 suffixes as lists e.g. CHI.1 and CHI.2 will be stored under "CHI" as a two-element list

    :param element: an xml element

    :return: a (possibly nested) dict
    """
    result = {
        k.lower(): sanitise(v)
        for k, v in element.attrib.items()
        if k not in ["type", "columns", "size"]
    }

    # Manually adding n information if it is missing
    if element.tag.startswith("PP_CHI") and "n" not in result and "label" in result:
        result["n"] = int(result["label"][0])

    # If the element has no children, extract the contents of element.text
    if len(element) == 0:
        if element.text is not None and element.text.strip():
            text = element.text.strip()
            try:
                value: Any = np.array(text.split(), dtype=float)
            except ValueError:
                value = text
            if result:
                result["content"] = value
            else:
                result = value
        return result  # type: ignore

    # If the element has children, extract the contents of each child
    for child in element:
        child_result = block_to_dict(child)
        tag = child.tag.split(".")[0].replace("PP_", "").lower()
        if tag in result or tag == "chi":
            if tag not in result:
                result[tag] = []
            elif not isinstance(result[tag], list):
                result[tag] = [result[tag]]
            result[tag].append(child_result)
        else:
            result[tag] = child_result

    return OrderedDict({k: result[k] for k in sorted(result)})


def upfv2contents_to_dict(filecontents: str):
    """Convert a string (corresponding to the contents of a UPF v2 file) into a nested dictionary."""
    root = defused_fromstring(filecontents)
    dct = block_to_dict(root)
    dct.pop("version")
    return dct


# ---------------------------------------------------------------------------
# Writing v2 UPF
# ---------------------------------------------------------------------------


def _format_array(arr: np.ndarray) -> str:
    """Format a numeric array as space-separated scientific notation.

    The result is wrapped at ``_DEFAULT_COLUMNS`` values per line to
    match the QE convention.

    :param arr: array of floats to format
    :returns: a string containing the formatted array, prefixed and suffixed with newlines
    """
    flat = np.asarray(arr).ravel()
    # 17 significant digits guarantees lossless float64 round-trip (IEEE 754).
    parts = [f"{v: .17E}" for v in flat]
    lines = [
        " ".join(parts[i : i + _DEFAULT_COLUMNS]) for i in range(0, len(parts), _DEFAULT_COLUMNS)
    ]
    return "\n" + "\n".join(lines) + "\n"


def _attr_value(value: Any) -> str:
    """Format a Python value as an XML attribute string."""
    if isinstance(value, bool):
        return "T" if value else "F"
    if isinstance(value, float):
        return f"{value:.17E}"
    return str(value)


def _set_array_attrs(elem: ElementTree.Element, arr: np.ndarray) -> None:
    """Populate the ``type/size/columns`` attribs on a numeric-array element."""
    elem.set("type", "real")
    elem.set("size", str(arr.size))
    elem.set("columns", str(_DEFAULT_COLUMNS))


def _is_array_like(value: Any) -> bool:
    return isinstance(value, np.ndarray)


def _make_pp_tag(name: str, index: int | None = None) -> str:
    """Convert a lower-case parser key back into a ``PP_<NAME>`` tag, optionally numbered."""
    tag = f"PP_{name.upper()}"
    if index is not None:
        tag = f"{tag}.{index}"
    return tag


def _build_element(tag: str, value: Any) -> ElementTree.Element:
    """Inverse of :func:`block_to_dict`: build an XML element from a parsed value.

    The shape of *value* drives behaviour:

    * ``np.ndarray`` -> bare numeric block with type/size/columns attribs
    * ``str`` -> element whose ``text`` is the raw string
    * ``Mapping`` -> attributes from non-``content`` keys; nested dicts/lists
      become child elements; a ``content`` key (if present) becomes the text
      of *this* element. Lists become numbered children.

    :param tag: tag name to give the new element
    :param value: parsed value to serialise
    :returns: a new :class:`xml.etree.ElementTree.Element`
    """
    elem = ElementTree.Element(tag)

    if _is_array_like(value):
        _set_array_attrs(elem, value)
        elem.text = _format_array(value)
        return elem

    if isinstance(value, str):
        # Wrap text content in newlines for readability (matches QE style).
        elem.text = "\n" + value.rstrip("\n") + "\n"
        return elem

    if isinstance(value, Mapping):
        # 1. Split the dict into (attribs, content, children).
        content: Any = None
        attribs: dict[str, Any] = {}
        children: dict[str, Any] = {}
        for k, v in value.items():
            if k == "content":
                content = v
            elif _is_array_like(v) or isinstance(v, (Mapping, list)):
                children[k] = v
            else:
                attribs[k] = v

        # 2. Emit attribs.
        for k, v in attribs.items():
            elem.set(k, _attr_value(v))

        # 3. Emit content (if present).
        if content is not None:
            if _is_array_like(content):
                _set_array_attrs(elem, content)
                elem.text = _format_array(content)
            elif isinstance(content, str):
                elem.text = "\n" + content.rstrip("\n") + "\n"
            else:
                elem.text = str(content)

        # 4. Emit children. Lists become numbered children; lone dicts
        #    use the bare PP_<NAME> tag. ``chi`` is always numbered, even
        #    with a single entry.
        for k, v in children.items():
            if isinstance(v, list):
                for i, item in enumerate(v, start=1):
                    elem.append(_build_element(_make_pp_tag(k, i), item))
            elif k in _ALWAYS_LIST_AS_INDEXED:
                elem.append(_build_element(_make_pp_tag(k, 1), v))
            else:
                elem.append(_build_element(_make_pp_tag(k), v))

        return elem

    # Fallback: stringify.
    elem.text = str(value)
    return elem


def dict_to_upfv2(upfdict: Mapping[str, Any], version: str) -> str:
    """Serialise a parsed UPF dictionary back to UPF v2 (XML) text.

    :param upfdict: mapping in the shape produced by :func:`upfv2contents_to_dict`
    :param version: UPF version string to record on the root ``<UPF version="...">``
    :returns: a complete UPF v2 file ready to be written to disk
    """
    root = ElementTree.Element("UPF", attrib={"version": str(version)})
    for k, v in upfdict.items():
        if isinstance(v, list):
            for i, item in enumerate(v, start=1):
                root.append(_build_element(_make_pp_tag(k, i), item))
        elif k in _ALWAYS_LIST_AS_INDEXED:
            root.append(_build_element(_make_pp_tag(k, 1), v))
        else:
            root.append(_build_element(_make_pp_tag(k), v))

    ElementTree.indent(root, space="  ")
    body = ElementTree.tostring(root, encoding="unicode")
    return body + "\n"
