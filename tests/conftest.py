"""Fixtures for use in the test suite."""

import builtins
import io
import os

import matplotlib.pyplot as plt
import pytest


def patch_open(open_func, files):
    """Wrap the function open_func to keep track of any files that have been created."""

    def open_patched(
        path,
        mode="r",
        buffering=-1,
        encoding=None,
        errors=None,
        newline=None,
        closefd=True,
        opener=None,
    ):
        """Call open_func while keeping track of the files that have been created."""
        if "w" in mode and not os.path.isfile(path):
            files.append(path)
        return open_func(
            path,
            mode=mode,
            buffering=buffering,
            encoding=encoding,
            errors=errors,
            newline=newline,
            closefd=closefd,
            opener=opener,
        )

    return open_patched


@pytest.fixture(autouse=True)
def cleanup_files(monkeypatch):
    """Delete any files that have been created once a test is complete."""
    files = []
    monkeypatch.setattr(builtins, "open", patch_open(builtins.open, files))
    monkeypatch.setattr(io, "open", patch_open(io.open, files))
    yield
    for file in files:
        os.remove(file)


@pytest.fixture(autouse=True)
def autoclose_figures():
    """Close all figures after each test."""
    yield
    plt.close("all")
