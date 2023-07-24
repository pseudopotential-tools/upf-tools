# -*- coding: utf-8 -*-

"""Command line interface for :mod:`upf_tools`.

Why does this file exist, and why not put this in ``__main__``? You might be tempted to import things from ``__main__``
later, but that will cause problems--the code will get executed twice:

- When you run ``python3 -m upf_tools`` python will execute``__main__.py`` as a script.
  That means there won't be any ``upf_tools.__main__`` in ``sys.modules``.
- When you import __main__ it will get executed again (as a module) because
  there's no ``upf_tools.__main__`` in ``sys.modules``.

.. seealso:: https://click.palletsprojects.com/en/8.1.x/setuptools/#setuptools-integration
"""

import logging

import click

from upf_tools import UPFDict

__all__ = [
    "main",
]

logger = logging.getLogger(__name__)


@click.group()
@click.version_option()
def main():
    """CLI for upf_tools."""


@main.command()
@click.argument("filename")
def to_input(filename):
    """
    Extract an input file from a pseudopotential.

    :param filename: the name of the .upf file
    :type filename: str
    """
    psp = UPFDict.from_upf(filename)
    inp = psp.to_input()
    click.echo(inp)


@main.command()
@click.argument("filename")
def to_dat(filename):
    """Extract a dat file from a pseudopotential.

    :param filename: the name of the .upf file
    :type filename: str
    """
    psp = UPFDict.from_upf(filename)
    dat = psp.to_dat()
    click.echo(dat)


if __name__ == "__main__":
    main()
