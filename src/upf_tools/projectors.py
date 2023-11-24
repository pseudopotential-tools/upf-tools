from collections import UserList
from dataclasses import dataclass, field
import numpy as np
from typing import TypeVar, Generic
from pathlib import Path
import matplotlib.pyplot as plt

ProjType = TypeVar('ProjType', bound='Projector')

@dataclass
class Projector:
   x: np.ndarray
   y: np.ndarray = np.zeros(1)
   l: int = 0
   _x: np.ndarray = field(init=False, repr=False)
   _x_min: float = field(default=-16, init=False, repr=False)

   @property
   def x(self):
      return self._x
   
   @x.setter
   def x(self, value):
      self._x = value
      self._x[self._x < self._x_min] = self._x_min

   @property
   def r(self):
      return np.exp(self.x)
   
   @r.setter
   def r(self, value):
      self.x = np.log(value)

   def plot(self, ax=None, **kwargs):
      if ax is None:
         _, ax = plt.subplots()
      if 'label' not in kwargs:
         kwargs['label'] = f'l={self.l}'

      ax.plot(self.r, self.y, **kwargs)

      return ax
   

# Create a class called Projectors that is a subclass of UserList that contains only Projector objects
class Projectors(UserList, Generic[ProjType]):
   
   def to_str(self) -> str:
      lines = [f'{len(self.data[0].x)} {len(self.data)}', ' '.join([str(proj.l) for proj in self.data])]
      content = np.concatenate([np.vstack([self.data[0].x, self.data[0].r]), [p.y for p in self.data]]).transpose()
      lines += [' '.join([f'{v:18.12e}' for v in row]) for row in content]
      return '\n'.join(lines)
   
   def to_file(self, filename: Path):
      with open(filename, 'w') as fd:
         fd.write(self.to_str())

   @classmethod
   def from_str(cls, string: str) -> 'Projectors':

      lines = [l for l in string.split('\n') if l]
      content = np.array([[float(v) for v in row.split()] for row in lines[2:]]).transpose()
      lvals = [int(l) for l in lines[1].split()]
      data = [Projector(content[0], y, l) for l, y in zip(lvals, content[2:])]

      return cls(data)

   @classmethod
   def from_file(cls, path: Path):
      with open(path, 'r') as fd:
         string = fd.read()
      return cls.from_str(string)
   
   def plot(self, ax=None, **kwargs):
      for d in self.data:
         ax = d.plot(ax, **kwargs)
      ax.legend()
      return ax
      
