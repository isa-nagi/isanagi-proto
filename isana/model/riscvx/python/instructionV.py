# from isana.isa import parameter, assembly, binary
# from isana.isa import signed

from .defs import xlen
# from .memory import Mem
# from .register import GPR, GPRC, CSR, PCR
from .instructionType import (
    InstrVLoadFP0,
    InstrVLoadFP1,
    InstrVLoadFP2,
    InstrVStoreFP0,
    InstrVStoreFP1,
    InstrVStoreFP2,
    InstrVArith0,
    InstrVArith12,
    InstrVArith3,
    InstrVArith45,
    InstrVArith6,
    InstrVConf0,
    InstrVConf1,
    InstrVConf2,
)


class vsetvli(InstrConf0):
    opn, opc = "vsetvli", 0b0_00000000000_00000_111_00000_1010111


class vsetivli(InstrConf1):
    opn, opc = "vsetivli", 0b1_1_0000000000_00000_111_00000_1010111


class vsetvl(InstrConf2):
    opn, opc = "vsetvl", 0b1_000000_00000_00000_111_00000_1010111


# RV32I
instructionsV = [
]
