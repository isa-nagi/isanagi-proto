# from isana.isa import parameter, assembly, binary
from isana.isa import signed, unsigned

from .defs import xlen
# from .memory import Mem
# from .register import GPR, GPRC, CSR, PCR
from .instructionType import (
    InstrR,
)


class mul(InstrR):
    subsets = ["ext-m"]
    opn, opc = "mul", 0b0000001_00000_00000_000_00000_0110011

    def semantic(self, ctx, ins):
        ctx.GPR[ins.rd] = ctx.GPR[ins.rs1] * ctx.GPR[ins.rs2]


class mulh(InstrR):
    subsets = ["ext-m"]
    opn, opc = "mulh", 0b0000001_00000_00000_001_00000_0110011

    def semantic(self, ctx, ins):
        ctx.GPR[ins.rd] = (ctx.GPR[ins.rs1] * ctx.GPR[ins.rs2]) << xlen


class mulhsu(InstrR):
    subsets = ["ext-m"]
    opn, opc = "mulhsu", 0b0000001_00000_00000_010_00000_0110011

    def semantic(self, ctx, ins):
        ctx.GPR[ins.rd] = (ctx.GPR[ins.rs1] * unsigned(xlen, ctx.GPR[ins.rs2])) << xlen


class mulhu(InstrR):
    subsets = ["ext-m"]
    opn, opc = "mulhu", 0b0000001_00000_00000_011_00000_0110011

    def semantic(self, ctx, ins):
        ctx.GPR[ins.rd] = (unsigned(xlen, ctx.GPR[ins.rs1]) * unsigned(xlen, ctx.GPR[ins.rs2])) << xlen


class div(InstrR):
    subsets = ["ext-m"]
    opn, opc = "div", 0b0000001_00000_00000_100_00000_0110011

    def semantic(self, ctx, ins):
        ctx.GPR[ins.rd] = ctx.GPR[ins.rs1] // ctx.GPR[ins.rs2]


class divu(InstrR):
    subsets = ["ext-m"]
    opn, opc = "divu", 0b0000001_00000_00000_101_00000_0110011

    def semantic(self, ctx, ins):
        ctx.GPR[ins.rd] = unsigned(xlen, ctx.GPR[ins.rs1]) // unsigned(xlen, ctx.GPR[ins.rs2])


class rem(InstrR):
    subsets = ["ext-m"]
    opn, opc = "rem", 0b0000001_00000_00000_110_00000_0110011

    def semantic(self, ctx, ins):
        ctx.GPR[ins.rd] = ctx.GPR[ins.rs1] % ctx.GPR[ins.rs2]


class remu(InstrR):
    subsets = ["ext-m"]
    opn, opc = "remu", 0b0000001_00000_00000_111_00000_0110011

    def semantic(self, ctx, ins):
        ctx.GPR[ins.rd] = unsigned(xlen, ctx.GPR[ins.rs1]) % unsigned(xlen, ctx.GPR[ins.rs2])


class mulw(InstrR):
    subsets = ["rv64", "ext-m"]
    opn, opc = "mulw", 0b0000001_00000_00000_000_00000_0111011

    def semantic(self, ctx, ins):
        ctx.GPR[ins.rd] = signed(32, ctx.GPR[ins.rs1] * ctx.GPR[ins.rs2])


class divw(InstrR):
    subsets = ["rv64", "ext-m"]
    opn, opc = "divw", 0b0000001_00000_00000_100_00000_0111011

    def semantic(self, ctx, ins):
        ctx.GPR[ins.rd] = signed(32, ctx.GPR[ins.rs1] // ctx.GPR[ins.rs2])


class divuw(InstrR):
    subsets = ["rv64", "ext-m"]
    opn, opc = "divuw", 0b0000001_00000_00000_101_00000_0111011

    def semantic(self, ctx, ins):
        ctx.GPR[ins.rd] = signed(32, unsigned(xlen, ctx.GPR[ins.rs1]) // unsigned(xlen, ctx.GPR[ins.rs2]))


class remw(InstrR):
    subsets = ["rv64", "ext-m"]
    opn, opc = "remw", 0b0000001_00000_00000_110_00000_0111011

    def semantic(self, ctx, ins):
        ctx.GPR[ins.rd] = signed(32, ctx.GPR[ins.rs1] % ctx.GPR[ins.rs2])


class remuw(InstrR):
    subsets = ["rv64", "ext-m"]
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
