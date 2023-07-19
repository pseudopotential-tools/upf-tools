from typing import Any, Dict, List
import numpy as np


def manually_get_xml_block(tag, lines: List[str]) -> List[str]:
    istart = next((i for i, line in enumerate(lines) if f"<{tag}" in line), None)

    if istart is None:
        raise ValueError(f"<{tag}> not found")

    ilength = next((i for i, line in enumerate(lines[istart:]) if f"</{tag}" in line), None)

    if ilength is None:
        raise ValueError(f"</{tag}> not found")

    return lines[istart : istart + ilength + 1]


def sanitise_pswfc(dct: Dict[str, Any]) -> Dict[str, Any]:
    lines = dct["content"]
    dct = {"chi": []}
    array = []
    for line in lines:
        if "Wavefunction" in line:
            if array:
                dct["chi"][-1]["content"] = np.array(array, dtype=float)
            label, l, occupation, _ = line.split()
            dct["chi"].append({"label": label, "l": l, "occupation": float(occupation)})
            array = []
        else:
            array += line.split()
    dct["chi"][-1]["content"] = np.array(array, dtype=float)
    return dct


def sanitise_beta(dct: Dict[str, Any]) -> Dict[str, Any]:
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
    lines = dct["content"]
    splitlines = [l.split() for l in lines]
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


def sanitise_numeric_array(dct: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitise a dict that only contains a numeric array"""
    array = np.array([v for row in dct["content"] for v in row.split()], dtype=float)
    return {"type": "real", "size": len(array), "content": array}


def sanitise_dij(dct: Dict[str, Any]) -> Dict[str, Any]:
    lines = dct["content"]
    length = max([int(l.split()[1]) for l in lines[1:]])
    content = np.zeros((length, length))
    for row in lines[1:]:
        i, j, val = row.split()
        content[int(i) - 1, int(j) - 1] = float(val)
    dct = {"type": "real", "size": length**2, "content": content}


def block_to_dict(lines):
    dct = {}

    # Parse the text
    inext = next((i for i, line in enumerate(lines) if line.strip().startswith("<")), None)
    textlines = lines if inext is None else lines[:inext]
    text = [l for l in textlines if l.strip()]
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
        tag = match.strip()[1:-1].split()[0]

        # Extract and parse that block
        block = manually_get_xml_block(tag, lines)

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
    lines = string.split("\n")
    return block_to_dict(lines)
