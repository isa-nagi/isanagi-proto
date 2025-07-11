# from isana.isa import parameter, assembly, binary
# from isana.isa import signed

# from .memory import Mem
# from .register import GPR, GPRC, CSR, PCR
from .instructionType import (
    InstrCSRR, InstrCSRI,
)


class csrrw(InstrCSRR):
    opn, opc = "csrrw", 0b000000000000_00000_001_00000_1110011

    def semantic(self, ctx, ins):
        t = ctx.GPR[ins.rs1]
        ctx.GPR[ins.rd] = ctx.CSR[ins.imm]
        ctx.CSR[ins.imm] = t


class csrrs(InstrCSRR):
    opn, opc = "csrrs", 0b000000000000_00000_010_00000_1110011


class csrrc(InstrCSRR):
    opn, opc = "csrrc", 0b000000000000_00000_011_00000_1110011


class csrrwi(InstrCSRI):
    opn, opc = "csrrwi", 0b000000000000_00000_101_00000_1110011


class csrrsi(InstrCSRI):
    opn, opc = "csrrsi", 0b000000000000_00000_110_00000_1110011


class csrrci(InstrCSRI):
    opn, opc = "csrrci", 0b000000000000_00000_111_00000_1110011


# Zicsr
instructionsZicsr = [
    csrrw,
    csrrs,
    csrrc,
    csrrwi,
    csrrsi,
    csrrci,
]
