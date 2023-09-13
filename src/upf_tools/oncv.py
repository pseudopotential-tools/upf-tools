"""
Classes for handling the oncv headers

"""

from typing import Optional, List
from dataclasses import dataclass

from upf_tools.utils import sanitise

class ONCVBlock:
   @property
   def header(self):
      return ' '.join(self.__dict__.keys())
   
   @property
   def content(self):
      return ' '.join([str(v) for v in self.__dict__.values()])
   
   def to_text(self):
      return f'{self.header}\n{self.content}'

   def __repr__(self):
      return str(self.__dict__)


@dataclass(repr=False)
class ONCVAtom(ONCVBlock):
   atsym: str
   z: float
   nc: int
   nv: int
   iexc: int
   psfile: str

@dataclass(repr=False)
class ONCVConfigurationSubshell(ONCVBlock):
   n: int
   l: int
   f: float

@dataclass(repr=False)
class ONCVConfiguration(ONCVBlock):
   subshells: List[ONCVConfigurationSubshell]

   def header(self):
      return self.subshells[0].header

   def content(self):
      return f'{len(self)}\n' + '\n'.join([subshell.content for subshell in self.subshells])

@dataclass(repr=False)
class ONCVConfigurations(ONCVBlock):
   configurations: List[ONCVConfiguration]

   def __len__(self):
      return len(self.configurations)

   def header(self):
      return self.configurations[0].header

   def content(self):
      return '\n'.join([configuration.content for configuration in self.configurations])

@dataclass(repr=False)
class ONCVOptimizationChannel(ONCVBlock):
   l: int
   rc: float
   ep: float
   ncon: int
   nbas: int
   qcut: float

@dataclass(repr=False)
class ONCVOptimization(ONCVBlock):
   channels: List[ONCVOptimizationChannel]

   def header(self):
      return self.channels[0].header

   def content(self):
      return '\n'.join([channel.content for channel in self.channels])

@dataclass(repr=False)
class ONCVLocalPotential(ONCVBlock):
   lloc: int
   lpopt: int
   rc: float
   dvloc0: float

@dataclass(repr=False)
class ONCVVKBProjector(ONCVBlock):
   l: int
   nproj: int
   debl: float

@dataclass(repr=False)
class ONCVModelCoreCharge(ONCVBlock):
   icmod: int
   fcfact: float
   rcfact: Optional[float] = None

@dataclass(repr=False)
class ONCVLogDerivativeAnalysis(ONCVBlock):
   epsh1: float
   epsh2: float
   depsh: float

@dataclass(repr=False)
class ONCVOutputGrid(ONCVBlock):
   rlmax: float
   drl: float

@dataclass
class ONCVInput:
   atom: ONCVAtom
   reference_configuration: ONCVConfiguration
   lmax: int
   optimization: ONCVOptimization
   local_potential: ONCVLocalPotential
   vkb_projectors: ONCVVKBProjector
   model_core_charge: ONCVModelCoreCharge
   log_derivative_analysis: ONCVLogDerivativeAnalysis
   output_grid: ONCVOutputGrid
   test_configurations: ONCVConfigurations

   @classmethod
   def from_file(cls, filename: str):
      with open(filename, 'r') as f:
         txt = f.read()
      return cls.from_text(txt)

   @classmethod
   def from_text(cls, txt: str):
      
      lines = [l.strip() for l in txt.split('\n')]

      content = [l for l in lines if not l.startswith('#')]

      # atom
      atom = ONCVAtom(*[sanitise(v) for v in content[0].split()])

      # reference configuration
      ntot = atom.nc + atom.nv
      reference_configuraton = ONCVConfiguration([ONCVConfigurationSubshell(*[sanitise(v) for v in line.split()]) for line in content[1:ntot + 1]])

      # lmax
      lmax = int(content[ntot+1])

      # optimization
      istart = ntot + 2
      iend = istart + lmax + 1
      optimization = ONCVOptimization([ONCVOptimizationChannel(*[sanitise(v) for v in line.split()]) for line in content[istart:iend]])

      ## UP TO HERE

      # local potential
      local_potential = ONCVLocalPotential(*[sanitise(v) for v in content[iend].split()])

      # VKB projectors
      istart = iend + 1
      iend = istart + lmax + 1
      vkb = [ONCVVKBProjector(*[sanitise(v) for v in line.split()]) for line in content[istart:iend]]

      # model core charge
      mcc = ONCVModelCoreCharge(*[sanitise(v) for v in content[iend].split()])
      iend += 1

      # log derivative analysis
      log_derivative_analysis = ONCVLogDerivativeAnalysis(*[sanitise(v) for v in content[iend].split()])
      iend += 1

      # output grid
      output_grid = ONCVOutputGrid(*[sanitise(v) for v in content[iend].split()])
      iend += 1

      # test configurations
      ncvf = int(content[iend])
      iend += 1
      test_configs = []
      for _ in range(ncvf):
         istart = iend + 1
         iend = istart + atom.nv
         test_configs.append(ONCVConfiguration[ONCVConfigurationSubshell(*[sanitise(v) for v in line.split()]) for line in content[istart:iend]])
      
      return cls()
      


      return oncvi

   def to_text(self):
      out = []
      for name, block in self.items():
         out.append(f'# {name.upper()}')
         if isinstance(block, int):
            out.append(str(block))
            continue
         if isinstance(block, dict):
            block = [block]
         out.append(' '.join(block[0].keys()))
         for line in block:
            out.append(' '.join([str(v) for v in line.values()]))
      return '\n'.join(out)
         