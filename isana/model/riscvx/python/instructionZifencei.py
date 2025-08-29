# from .memory import Mem
# from .register import GPR, GPRC, CSR, PCR
from .instructionType import (
    InstrIFencei,
)


class fence_i(InstrIFencei):
    subsets = ["ext-zifencei"]
    opn, opc = "fence.i", 0b000000000000_00000_001_00000_0001111


# Zifencei
instructionsZifencei = [
    fence_i,
]
