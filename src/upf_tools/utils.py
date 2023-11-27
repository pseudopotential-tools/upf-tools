"""Miscellaneous utilities for upf-tools."""

import json
import re
import warnings
from typing import Any

from packaging.version import Version

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


def sanitise(value: str) -> Any:
    """Convert an arbitrary string to an int/float/bool if it appears to be one of these."""
    try:
        value = json.loads(value)
    except json.decoder.JSONDecodeError:
        pass
    return value
