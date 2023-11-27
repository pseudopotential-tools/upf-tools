"""Module that supports the projector file format for ``pw2wannier90`` and ``Wannier90``."""

from collections import UserList
from dataclasses import dataclass, field
from pathlib import Path
from typing import Generic, TypeVar

import matplotlib.pyplot as plt
import numpy as np

ProjType = TypeVar("ProjType", bound="Projector")


@dataclass
class Projector:
    """A single projector."""

    x: np.ndarray
    y: np.ndarray = field(default_factory=lambda: np.array([]))
    l: int = 0
    _x: np.ndarray = field(init=False, repr=False)
    _x_min: float = field(default=-16, init=False, repr=False)

    @property  # type: ignore[no-redef]
    def x(self):
        """Return the logarithmic radial grid."""
        return self._x

    @x.setter
    def x(self, value):
        self._x = value
        self._x[self._x < self._x_min] = self._x_min

    @property
    def r(self):
        """The radial grid."""
        return np.exp(self.x)

    @r.setter
    def r(self, value):
        self.x = np.log(value)

    def plot(self, ax=None, **kwargs):
        """Plot the projector."""
        if ax is None:
            _, ax = plt.subplots()
        if "label" not in kwargs:
            kwargs["label"] = f"l={self.l}"

        ax.plot(self.r, self.y, **kwargs)

        return ax


class Projectors(UserList, Generic[ProjType]):
    """A list of projectors, with few extra functionalities."""

    def to_str(self) -> str:
        """Convert the Projectors into a string following the format for ``pw2wannier90`` and ``Wannier90``."""
        lines = [
            f"{len(self.data[0].x)} {len(self.data)}",
            " ".join([str(proj.l) for proj in self.data]),
        ]
        content = np.concatenate(
            [np.vstack([self.data[0].x, self.data[0].r]), [p.y for p in self.data]]
        ).transpose()
        lines += [" ".join([f"{v:18.12e}" for v in row]) for row in content]
        return "\n".join(lines)

    def to_file(self, filename: Path):
        """Dump the Projectors to a file following the format for ``pw2wannier90`` and ``Wannier90``."""
        with open(filename, "w") as fd:
            fd.write(self.to_str())

    @classmethod
    def from_str(cls, string: str) -> "Projectors":
        """Create a Projectors object from a string that follows the format for ``pw2wannier90`` and ``Wannier90``."""
        lines = [l for l in string.split("\n") if l]
        content = np.array([[float(v) for v in row.split()] for row in lines[2:]]).transpose()
        lvals = [int(l) for l in lines[1].split()]
        data = [Projector(content[0], y, l) for l, y in zip(lvals, content[2:])]

        return cls(data)

    @classmethod
    def from_file(cls, path: Path):
        """Create a Projectors object from a file that follows the format for ``pw2wannier90`` and ``Wannier90``."""
        with open(path, "r") as fd:
            string = fd.read()
        return cls.from_str(string)

    def plot(self, ax=None, **kwargs):
        """Plot all the projectors."""
        for d in self.data:
            ax = d.plot(ax, **kwargs)
        ax.legend()
        return ax
