"""Miscellaneous utilities for upf-tools."""

import re
import warnings

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
