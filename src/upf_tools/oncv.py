"""Classes for handling ONCV input files."""

from dataclasses import dataclass
from typing import List, Optional

from upf_tools.utils import sanitise


class ONCVBlock:
    """Generic class for an object in an ONCV input file."""

    @property
    def columns(self):
        """Return the column headers for the block."""
        return "# " + " ".join([f"{str(k): >8}" for k in self.__dict__.keys()])[2:]

    @property
    def content(self):
        """Return the content of the block."""
        return " ".join([f"{str(v): >8}" for v in self.__dict__.values() if v is not None])

    def to_str(self):
        """Return the text representation of the block."""
        return f"{self.columns}\n{self.content}"

    def __repr__(self):
        """Make the repr of the block very simple."""
        return str(self.__dict__)


@dataclass(repr=False)
class ONCVAtom(ONCVBlock):
    """Class for the atom block in an ONCV input file."""

    atsym: str
    z: float
    nc: int
    nv: int
    iexc: int
    psfile: str


@dataclass(repr=False)
class ONCVConfigurationSubshell(ONCVBlock):
    """Class for a subshell in an ONCV configuration block."""

    n: int
    l: int
    f: float


@dataclass(repr=False)
class ONCVConfiguration(ONCVBlock):
    """Class for a configuration in an ONCV input file."""

    subshells: List[ONCVConfigurationSubshell]
    print_length: bool = True

    def __len__(self):
        """Return the number of subshells in the configuration."""
        return len(self.subshells)

    @property
    def columns(self):
        """Return the column headers for the block."""
        return self.subshells[0].columns

    @property
    def content(self):
        """Return the content of the block."""
        out = ""
        if self.print_length:
            out = f"{len(self): >8}\n"
        out += "\n".join([subshell.content for subshell in self.subshells])
        return out


@dataclass(repr=False)
class ONCVConfigurations(ONCVBlock):
    """Class for a list of configurations in an ONCV input file."""

    configurations: List[ONCVConfiguration]

    def __len__(self):
        """Return the number of configurations in the block."""
        return len(self.configurations)

    @property
    def columns(self):
        """Return the column headers for the block."""
        return self.configurations[0].columns

    @property
    def content(self):
        """Return the content of the block."""
        return "\n".join([configuration.content for configuration in self.configurations])


@dataclass(repr=False)
class ONCVOptimizationChannel(ONCVBlock):
    """Class for an optimization channel in an ONCV input file."""

    l: int
    rc: float
    ep: float
    ncon: int
    nbas: int
    qcut: float


@dataclass(repr=False)
class ONCVOptimization(ONCVBlock):
    """Class for the optimization block in an ONCV input file."""

    channels: List[ONCVOptimizationChannel]

    @property
    def columns(self):
        """Return the column headers for the block."""
        return self.channels[0].columns

    @property
    def content(self):
        """Return the content of the block."""
        return "\n".join([channel.content for channel in self.channels])


@dataclass(repr=False)
class ONCVLocalPotential(ONCVBlock):
    """Class for the local potential block in an ONCV input file."""

    lloc: int
    lpopt: int
    rc: float
    dvloc0: float


@dataclass(repr=False)
class ONCVVKBProjector(ONCVBlock):
    """Class for a VKB projector in an ONCV input file."""

    l: int
    nproj: int
    debl: float


@dataclass(repr=False)
class ONCVVKBProjectors(ONCVBlock):
    """Class for the VKB projectors block in an ONCV input file."""

    projectors: List[ONCVVKBProjector]

    @property
    def columns(self):
        """Return the column headers for the block."""
        return self.projectors[0].columns

    @property
    def content(self):
        """Return the content of the block."""
        return "\n".join([projector.content for projector in self.projectors])


@dataclass(repr=False)
class ONCVModelCoreCharge(ONCVBlock):
    """Class for the model core charge block in an ONCV input file."""

    icmod: int
    fcfact: float
    rcfact: Optional[float] = None


@dataclass(repr=False)
class ONCVLogDerivativeAnalysis(ONCVBlock):
    """Class for the log derivative analysis block in an ONCV input file."""

    epsh1: float
    epsh2: float
    depsh: float


@dataclass(repr=False)
class ONCVOutputGrid(ONCVBlock):
    """Class for the output grid block in an ONCV input file."""

    rlmax: float
    drl: float


@dataclass
class ONCVInput:
    """Class for the contents of an ONCV input file."""

    atom: ONCVAtom
    reference_configuration: ONCVConfiguration
    lmax: int
    optimization: ONCVOptimization
    local_potential: ONCVLocalPotential
    vkb_projectors: ONCVVKBProjectors
    model_core_charge: ONCVModelCoreCharge
    log_derivative_analysis: ONCVLogDerivativeAnalysis
    output_grid: ONCVOutputGrid
    test_configurations: ONCVConfigurations

    @classmethod
    def from_file(cls, filename: str):
        """Create an :class:`ONCVInput` object from an ONCV input file."""
        with open(filename, "r") as f:
            txt = f.read()
        return cls.from_str(txt)

    @classmethod
    def from_str(cls, txt: str):
        """Create an :class:`ONCVInput` object from a string."""
        lines = [line.strip() for line in txt.split("\n")]

        content = [line for line in lines if not line.startswith("#")]

        # atom
        atom = ONCVAtom(*[sanitise(v) for v in content[0].split()])

        # reference configuration
        ntot = atom.nc + atom.nv
        reference_configuraton = ONCVConfiguration(
            [
                ONCVConfigurationSubshell(*[sanitise(v) for v in line.split()])
                for line in content[1 : ntot + 1]
            ],
            print_length=False,
        )

        # lmax
        lmax = int(content[ntot + 1])

        # optimization
        istart = ntot + 2
        iend = istart + lmax + 1
        optimization = ONCVOptimization(
            [
                ONCVOptimizationChannel(*[sanitise(v) for v in line.split()])
                for line in content[istart:iend]
            ]
        )

        # local potential
        local_potential = ONCVLocalPotential(*[sanitise(v) for v in content[iend].split()])

        # VKB projectors
        istart = iend + 1
        iend = istart + lmax + 1
        vkb = ONCVVKBProjectors(
            [
                ONCVVKBProjector(*[sanitise(v) for v in line.split()])
                for line in content[istart:iend]
            ]
        )

        # model core charge
        mcc = ONCVModelCoreCharge(*[sanitise(v) for v in content[iend].split()])
        iend += 1

        # log derivative analysis
        log_derivative_analysis = ONCVLogDerivativeAnalysis(
            *[sanitise(v) for v in content[iend].split()]
        )
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
            test_configs.append(
                ONCVConfiguration(
                    [
                        ONCVConfigurationSubshell(*[sanitise(v) for v in line.split()])
                        for line in content[istart:iend]
                    ]
                )
            )

        return cls(
            atom,
            reference_configuraton,
            lmax,
            optimization,
            local_potential,
            vkb,
            mcc,
            log_derivative_analysis,
            output_grid,
            ONCVConfigurations(test_configs),
        )

    def to_str(self):
        """Return the text representation of the ONCV input file."""
        return "\n".join(
            [
                "# ATOM AND REFERENCE CONFIGURATION",
                self.atom.to_str(),
                self.reference_configuration.to_str(),
                "# PSEUDOPOTENTIAL AND OPTIMIZATION",
                "#   lmax",
                f"{self.lmax: >8}",
                self.optimization.to_str(),
                "# LOCAL POTENTIAL",
                self.local_potential.to_str(),
                "# VANDERBILT-KLEINMAN-BYLANDER PROJECTORS",
                self.vkb_projectors.to_str(),
                "# MODEL CORE CHARGE",
                self.model_core_charge.to_str(),
                "# LOG DERIVATIVE ANALYSIS",
                self.log_derivative_analysis.to_str(),
                "# OUTPUT GRID",
                self.output_grid.to_str(),
                "# TEST CONFIGURATIONS",
                "# ncnf",
                f"{len(self.test_configurations): >8}",
                self.test_configurations.to_str(),
            ]
        )

    def to_file(self, filename: str):
        """Write the ONCV input file to disk."""
        with open(filename, "w") as f:
            f.write(self.to_str())
