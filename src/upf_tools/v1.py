"""Functions for parsing UPF v1 files."""

from typing import Any, Dict, List

import numpy as np
from numpy.typing import NDArray


def extract_block(tag, lines: List[str]) -> List[str]:
    """Extract an block starting <tag> and ending </tag> from lines of text."""
    istart = next((i for i, line in enumerate(lines) if f"<{tag}" in line), None)

    if istart is None:
        raise ValueError(f"<{tag}> not found")

    ilength = next((i for i, line in enumerate(lines[istart:]) if f"</{tag}" in line), None)

    if ilength is None:
        raise ValueError(f"</{tag}> not found")

    return lines[istart : istart + ilength + 1]


def sanitise_pswfc(dct: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitise a PSWFC entry that has been read in with the default reader."""
    lines = dct["content"]
    dct = {"chi": []}
    array: List[str] = []
    for line in lines:
        if "Wavefunction" in line:
            if array:
                dct["chi"][-1]["content"] = np.array(array, dtype=float)
            label, l, occupation, _ = line.split()
            dct["chi"].append(
                {"label": label, "n": int(label[0]), "l": l, "occupation": float(occupation)}
            )
            array = []
        else:
            array += line.split()
    dct["chi"][-1]["content"] = np.array(array, dtype=float)
    return dct


def sanitise_beta(dct: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitise a BETA entry that has been read in with the default reader."""
    lines = dct["content"]
    index, l, beta, _ = lines[0].split()
    assert beta == "Beta"
    ncols = len(lines[2].split())
    array = np.array([v for row in lines[2:] for v in row.split()], dtype=float)
    dct = {
        "type": "real",
        "size": len(array),
        "columns": ncols,
        "index": int(index),
        "angular_momentum": int(l),
        "content": array,
    }
    return dct


def sanitise_header(dct: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitise a HEADER entry that has been read in with the default reader."""
    lines = dct["content"]
    splitlines = [line.split() for line in lines]
    dct = {
        "element": splitlines[1][0],
        "is_ultrasoft": splitlines[2][0] == "US",
        "core_correction": splitlines[3][0] == "T",
        "functional": " ".join(splitlines[4][:-3]),
        "z_valence": float(splitlines[5][0]),
        "total_psenergy": float(splitlines[6][0]),
        "rho_cutoff": float(splitlines[7][1]),
        "l_max": int(splitlines[8][0]),
        "mesh_size": int(splitlines[9][0]),
        "number_of_wfc": int(splitlines[10][0]),
        "number_of_proj": int(splitlines[10][1]),
    }

    return dct


def sanitise_numeric_array(dct: Dict[str, Any]) -> NDArray[np.float_]:
    """Sanitise a dict that only contains a numeric array."""
    array = np.array([v for row in dct["content"] for v in row.split()], dtype=float)
    return array


def sanitise_dij(dct: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitise a DIJ entry that has been read in with the default reader."""
    lines = dct["content"]
    length = max([int(line.split()[1]) for line in lines[1:]])
    content = np.zeros((length, length))
    for row in lines[1:]:
        i, j, val = row.split()
        content[int(i) - 1, int(j) - 1] = float(val)
    dct = {"type": "real", "size": length**2, "content": content}
    return dct


def block_to_dict(lines: List[str]) -> Dict[str, Any]:
    """Convert a block of lines from a UPF v1 file into a nested dictionary."""
    dct: Dict[str, Any] = {}

    # Parse the text
    inext = next((i for i, line in enumerate(lines) if line.strip().startswith("<")), None)
    textlines = lines if inext is None else lines[:inext]
    text = [line for line in textlines if line.strip()]
    if len(text) > 0:
        dct["content"] = text

    # Loop over children
    while True:
        # Find the next child
        inext, match = next(
            ((i, line) for i, line in enumerate(lines) if line.strip().startswith("<")),
            (None, None),
        )
        if inext is None:
            # If there are no more tags, we are finished
            break
        assert match is not None
        tag = match.strip()[1:-1].split()[0]

        # Extract and parse that block
        block = extract_block(tag, lines)

        # Remove everything up to the end of the new block
        del lines[: inext + len(block)]

        # Parse the contents of the block with a generic parser
        subdct = block_to_dict(block[1:-1])
        tag = tag.replace("PP_", "").lower()

        # Sanitise particular blocks
        sanitisers = {
            "pswfc": sanitise_pswfc,
            "header": sanitise_header,
            "r": sanitise_numeric_array,
            "rab": sanitise_numeric_array,
            "nlcc": sanitise_numeric_array,
            "local": sanitise_numeric_array,
            "beta": sanitise_beta,
            "dij": sanitise_dij,
            "rhoatom": sanitise_numeric_array,
        }
        if tag in sanitisers:
            subdct = sanitisers[tag](subdct)

        # Store the dict
        if tag in dct:
            if not isinstance(dct[tag], list):
                dct[tag] = [dct[tag]]
            dct[tag].append(subdct)
        else:
            dct[tag] = subdct
    return dct


def upfv1contents_to_dict(string: str) -> Dict[str, Any]:
    """Convert the contents of a UPF v1 file into a nested dictionary."""
    lines = string.split("\n")
    return block_to_dict(lines)
