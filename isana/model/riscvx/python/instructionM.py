# from isana.isa import parameter, assembly, binary
from isana.isa import signed, unsigned

from .defs import xlen
# from .memory import Mem
# from .register import GPR, GPRC, CSR, PCR
from .instructionType import (
    InstrR,
)


class mul(InstrR):
    opn, opc = "mul", 0b0000001_00000_00000_000_00000_0110011

    def semantic(self, ctx, ins):
        ctx.GPR[ins.rd] = ctx.GPR[ins.rs1] * ctx.GPR[ins.rs2]


class mulh(InstrR):
    opn, opc = "mulh", 0b0000001_00000_00000_001_00000_0110011

    def semantic(self, ctx, ins):
        ctx.GPR[ins.rd] = (ctx.GPR[ins.rs1] * ctx.GPR[ins.rs2]) << xlen


class mulhsu(InstrR):
    opn, opc = "mulhsu", 0b0000001_00000_00000_010_00000_0110011

    def semantic(self, ctx, ins):
        ctx.GPR[ins.rd] = (ctx.GPR[ins.rs1] * unsigned(xlen, ctx.GPR[ins.rs2])) << xlen


class mulhu(InstrR):
    opn, opc = "mulhu", 0b0000001_00000_00000_011_00000_0110011

    def semantic(self, ctx, ins):
        ctx.GPR[ins.rd] = (unsigned(xlen, ctx.GPR[ins.rs1]) * unsigned(xlen, ctx.GPR[ins.rs2])) << xlen


class div(InstrR):
    opn, opc = "div", 0b0000001_00000_00000_100_00000_0110011

    def semantic(self, ctx, ins):
        ctx.GPR[ins.rd] = ctx.GPR[ins.rs1] // ctx.GPR[ins.rs2]


class divu(InstrR):
    opn, opc = "divu", 0b0000001_00000_00000_101_00000_0110011

    def semantic(self, ctx, ins):
        ctx.GPR[ins.rd] = unsigned(xlen, ctx.GPR[ins.rs1]) // unsigned(xlen, ctx.GPR[ins.rs2])


class rem(InstrR):
    opn, opc = "rem", 0b0000001_00000_00000_110_00000_0110011

    def semantic(self, ctx, ins):
        ctx.GPR[ins.rd] = ctx.GPR[ins.rs1] % ctx.GPR[ins.rs2]


class remu(InstrR):
    opn, opc = "remu", 0b0000001_00000_00000_111_00000_0110011

    def semantic(self, ctx, ins):
        ctx.GPR[ins.rd] = unsigned(xlen, ctx.GPR[ins.rs1]) % unsigned(xlen, ctx.GPR[ins.rs2])


class mulw(InstrR):
    opn, opc = "mulw", 0b0000001_00000_00000_000_00000_0111011

    def semantic(self, ctx, ins):
        ctx.GPR[ins.rd] = signed(32, ctx.GPR[ins.rs1] * ctx.GPR[ins.rs2])


class divw(InstrR):
    opn, opc = "divw", 0b0000001_00000_00000_100_00000_0111011

    def semantic(self, ctx, ins):
        ctx.GPR[ins.rd] = signed(32, ctx.GPR[ins.rs1] // ctx.GPR[ins.rs2])


class divuw(InstrR):
    opn, opc = "divuw", 0b0000001_00000_00000_101_00000_0111011

    def semantic(self, ctx, ins):
        ctx.GPR[ins.rd] = signed(32, unsigned(xlen, ctx.GPR[ins.rs1]) // unsigned(xlen, ctx.GPR[ins.rs2]))


class remw(InstrR):
    opn, opc = "remw", 0b0000001_00000_00000_110_00000_0111011

    def semantic(self, ctx, ins):
        ctx.GPR[ins.rd] = signed(32, ctx.GPR[ins.rs1] % ctx.GPR[ins.rs2])


class remuw(InstrR):
    opn, opc = "remuw", 0b0000001_00000_00000_111_00000_0111011

    def semantic(self, ctx, ins):
        ctx.GPR[ins.rd] = signed(32, unsigned(xlen, ctx.GPR[ins.rs1]) % unsigned(xlen, ctx.GPR[ins.rs2]))


# M
instructionsM = [
    mul,
    mulh,
    mulhsu,
    mulhu,
    div,
    divu,
    rem,
    remu,
]

if xlen == 64:
    instructionsM += [
        mulw,
        divw,
        divuw,
        remw,
        remuw,
    ]
