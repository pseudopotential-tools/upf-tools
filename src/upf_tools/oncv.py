"""Classes for handling ONCV input files."""

from collections import UserList
from dataclasses import dataclass
from typing import Generic, Optional, TypeVar

from upf_tools.utils import sanitise


class ONCVEntry:
    """Generic class for an entry in an ONCV input file."""

    @property
    def columns(self):
        """Return the column headers for the entry."""
        return "# " + " ".join([f"{str(k): >8}" for k in self.__dict__.keys()])[2:]

    @property
    def content(self):
        """Return the content of the entry."""
        return " ".join([f"{str(v): >8}" for v in self.__dict__.values() if v is not None])

    def to_str(self):
        """Return the text representation of the entry."""
        return f"{self.columns}\n{self.content}"

    def __repr__(self):
        """Make the repr of the entry very simple."""
        return str(self.__dict__)


T = TypeVar("T")


class ONCVList(UserList, Generic[T]):
    """Generic class for an entry in an ONCV input file that contains multiple elements and emulates a list."""

    def __init__(self, data, print_length=False):
        self.print_length = print_length
        super().__init__(data)

    @property
    def columns(self):
        """Return the column headers for the list."""
        return self.data[0].columns

    @property
    def content(self):
        """Return the content of the list."""
        out = ""
        if self.print_length:
            out = f"{len(self): >8}\n"
        out += "\n".join([d.content for d in self.data])
        return out

    def to_str(self):
        """Return the text representation of the list."""
        return f"{self.columns}\n{self.content}"


@dataclass(repr=False)
class ONCVAtom(ONCVEntry):
    """Class for the atom block in an ONCV input file."""

    atsym: str
    z: float
    nc: int
    nv: int
    iexc: int
    psfile: str


@dataclass(repr=False)
class ONCVConfigurationSubshell(ONCVEntry):
    """Class for a subshell in an ONCV configuration block."""

    n: int
    l: int
    f: float


@dataclass(repr=False)
class ONCVOptimizationChannel(ONCVEntry):
    """Class for an optimization channel in an ONCV input file."""

    l: int
    rc: float
    ep: float
    ncon: int
    nbas: int
    qcut: float


@dataclass(repr=False)
class ONCVLocalPotential(ONCVEntry):
    """Class for the local potential block in an ONCV input file."""

    lloc: int
    lpopt: int
    rc: float
    dvloc0: float


@dataclass(repr=False)
class ONCVVKBProjector(ONCVEntry):
    """Class for a VKB projector in an ONCV input file."""

    l: int
    nproj: int
    debl: float


@dataclass(repr=False)
class ONCVModelCoreCharge(ONCVEntry):
    """Class for the model core charge block in an ONCV input file."""

    icmod: int
    fcfact: float
    rcfact: Optional[float] = None


@dataclass(repr=False)
class ONCVLogDerivativeAnalysis(ONCVEntry):
    """Class for the log derivative analysis block in an ONCV input file."""

    epsh1: float
    epsh2: float
    depsh: float


@dataclass(repr=False)
class ONCVOutputGrid(ONCVEntry):
    """Class for the output grid block in an ONCV input file."""

    rlmax: float
    drl: float


@dataclass
class ONCVInput:
    """Class for the contents of an ONCV input file."""

    atom: ONCVAtom
    reference_configuration: ONCVList[ONCVConfigurationSubshell]
    lmax: int
    optimization: ONCVList[ONCVOptimizationChannel]
    local_potential: ONCVLocalPotential
    vkb_projectors: ONCVList[ONCVVKBProjector]
    model_core_charge: ONCVModelCoreCharge
    log_derivative_analysis: ONCVLogDerivativeAnalysis
    output_grid: ONCVOutputGrid
    test_configurations: ONCVList[ONCVList[ONCVConfigurationSubshell]]

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
        reference_configuration: ONCVList[ONCVConfigurationSubshell] = ONCVList(
            [
                ONCVConfigurationSubshell(*[sanitise(v) for v in line.split()])
                for line in content[1 : ntot + 1]
            ]
        )

        # lmax
        lmax = int(content[ntot + 1])

        # optimization
        istart = ntot + 2
        iend = istart + lmax + 1
        optimization: ONCVList[ONCVOptimizationChannel] = ONCVList(
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
        vkb: ONCVList[ONCVVKBProjector] = ONCVList(
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
        test_configs: ONCVList[ONCVList[ONCVConfigurationSubshell]] = ONCVList([])
        for _ in range(ncvf):
            istart = iend + 1
            iend = istart + atom.nv
            test_configs.append(
                ONCVList(
                    [
                        ONCVConfigurationSubshell(*[sanitise(v) for v in line.split()])
                        for line in content[istart:iend]
                    ],
                    print_length=True,
                )
            )

        return cls(
            atom,
            reference_configuration,
            lmax,
            optimization,
            local_potential,
            vkb,
            mcc,
            log_derivative_analysis,
            output_grid,
            test_configs,
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
