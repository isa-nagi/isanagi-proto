# from .memory import Mem
# from .register import GPR, GPRC, CSR, PCR
from .instructionType import (
    InstrO,
)


class wrs_nto(InstrO):
    subsets = ["ext-zawrs"]
    opn, opc = "wrs.nto", 0b000000001101_00000_000_00000_1110011


class wrs_sto(InstrO):
    subsets = ["ext-zawrs"]
    opn, opc = "wrs.sto", 0b000000011101_00000_000_00000_1110011


# Zawrs
instructionsZawrs = [
    wrs_nto,
    wrs_sto,
]
